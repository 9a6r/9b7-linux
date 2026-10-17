import sqlite3
import tempfile
from pathlib import Path
import unittest
from nineb7.business import BusinessStore, BusinessError, money


class BusinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "institution.sqlite3"
        self.store = BusinessStore(self.path)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def organization(self):
        self.store.save_organization("شركة النور", "صيانة", "EGP", "ar")

    def test_first_launch_is_empty_and_language_persists(self):
        self.assertIsNone(self.store.organization())
        self.assertEqual(self.store.dashboard()["customers"], 0)
        self.organization()
        self.store.close()
        self.store = BusinessStore(self.path)
        self.assertEqual(self.store.organization()["language"], "ar")
        self.assertEqual(self.store.organization()["name"], "شركة النور")

    def test_arabic_crud_search_and_sql_metacharacters(self):
        key = self.store.save_customer("أحمد علي", "010123")
        self.assertEqual(self.store.records("customers", "أحمد")[0]["id"], key)
        self.store.save_customer("أحمد محمود", record_id=key)
        self.assertEqual(len(self.store.records("customers")), 1)
        self.assertEqual(self.store.records("customers", "' OR 1=1 --"), [])
        self.assertEqual(len(self.store.audit()), 2)

    def test_invoice_atomic_stock_price_snapshot_and_currency_lock(self):
        self.organization()
        customer = self.store.save_customer("Customer")
        product = self.store.save_product("A", "قطعة غيار", "10.25", 5)
        self.store.post_invoice(customer, [(product, 2)])
        self.assertEqual(self.store.dashboard()["sales_minor"], 2050)
        self.assertEqual(self.store.records("products")[0]["stock"], 3)
        self.store.save_product("A", "Updated", "20", 3, product)
        self.assertEqual(self.store.invoices()[0]["total_minor"], 2050)
        self.assertEqual(self.store.db.execute("SELECT description FROM invoice_lines").fetchone()[0], "قطعة غيار")
        with self.assertRaisesRegex(BusinessError, "currency_locked"):
            self.store.save_organization("Company", "Retail", "USD", "en")

    def test_oversale_rolls_back_everything_and_duplicate_lines_are_merged(self):
        self.organization()
        customer = self.store.save_customer("Customer")
        a = self.store.save_product("A", "A", "1.50", 10)
        b = self.store.save_product("B", "B", "2", 1)
        before = len(self.store.audit())
        with self.assertRaisesRegex(BusinessError, "insufficient_stock"):
            self.store.post_invoice(customer, [(a, 5), (b, 2)])
        self.assertEqual(self.store.records("products")[0]["stock"], 10)
        self.assertEqual(self.store.invoices(), [])
        self.assertEqual(len(self.store.audit()), before)
        self.store.post_invoice(customer, [(a, 2), (a, 1)])
        self.assertEqual(self.store.dashboard()["sales_minor"], 450)

    def test_backup_restore_preserves_old_database_and_rejects_foreign_files(self):
        self.organization()
        self.store.save_customer("Original")
        backup = self.store.backup(Path(self.tmp.name) / "backup.sqlite3")
        self.store.save_customer("Later")
        saved = self.store.restore(backup)
        self.assertTrue(saved.exists())
        self.assertEqual(len(self.store.records("customers")), 1)
        with sqlite3.connect(saved) as con:
            self.assertEqual(con.execute("SELECT count(*) FROM customers").fetchone()[0], 2)
        bad = Path(self.tmp.name) / "bad.sqlite3"
        bad.write_text("not a database")
        with self.assertRaises(BusinessError):
            self.store.restore(bad)
        self.assertEqual(len(self.store.records("customers")), 1)
        with self.assertRaisesRegex(BusinessError, "file_exists"):
            self.store.backup(backup)

    def test_money_is_exact_and_rejects_nonfinite_or_fractional_cents(self):
        self.assertEqual(money("123.45"), 12345)
        for value in ("NaN", "Infinity", "-1", "1.001", "abc"):
            with self.assertRaises(BusinessError):
                money(value)

    def test_newer_schema_is_not_overwritten(self):
        self.store.db.execute("PRAGMA user_version=99")
        with self.assertRaisesRegex(BusinessError, "incompatible_database"):
            BusinessStore(self.path)
        self.assertEqual(self.store.db.execute("PRAGMA user_version").fetchone()[0], 99)


if __name__ == "__main__":
    unittest.main()
