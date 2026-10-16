import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from nineb7 import flow, databases, agents

HEADER = "order_id,date,customer,product,quantity,unit_price,unit_cost\n"


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "business.sqlite3"
        self.csv = self.root / "sales.csv"

    def run_csv(self, text, strict=False):
        self.csv.write_text(HEADER + text)
        return flow.run(self.csv, self.db, self.root / "reports", strict)

    def test_money_and_kpis_and_idempotent_import(self):
        text = "001,2026-10-01,Nile,Widget,3,10.10,4.10\n"
        first = self.run_csv(text)
        self.assertEqual(first["kpis"]["revenue"], 30.3)
        self.assertEqual(first["kpis"]["profit"], 18)
        second = self.run_csv(text)
        self.assertEqual(second["inserted"], 0)
        self.assertEqual(second["duplicates"], 1)
        self.assertEqual(second["kpis"]["orders"], 1)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select count(*) from runs").fetchone()[0], 2)

    def test_invalid_rows_are_audited(self):
        result = self.run_csv("a,2026-10-01,Nile,Good,1,10,4\nb,bad,Nile,Bad,1,10,4\n")
        self.assertEqual((result["inserted"], result["rejected"]), (1, 1))
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select line from rejections").fetchone()[0], 3)

    def test_strict_rejects_without_importing(self):
        with self.assertRaises(ValueError):
            self.run_csv("a,2026-10-01,Nile,Good,1,10,4\nb,invalid,Nile,Bad,1,10,4\n", True)
        self.assertFalse(self.db.exists())

    def test_conflicting_id_is_not_silently_overwritten(self):
        self.run_csv("a,2026-10-01,Nile,Good,1,10,4\n")
        result = self.run_csv("a,2026-10-01,Nile,Good,2,10,4\n")
        self.assertEqual(result["rejected"], 1)
        self.assertEqual(result["kpis"]["revenue"], 10)

    def test_strict_conflict_rolls_back_whole_transaction(self):
        self.run_csv("a,2026-10-01,Nile,Good,1,10,4\n")
        with self.assertRaises(ValueError):
            self.run_csv("b,2026-10-01,Nile,Good,1,10,4\na,2026-10-01,Nile,Good,9,10,4\n", True)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute("select count(*) from orders").fetchone()[0], 1)
            self.assertEqual(db.execute("select count(*) from runs").fetchone()[0], 1)

    def test_nonfinite_and_negative_money_are_rejected(self):
        for value in ["NaN", "Infinity", "-1", "1000000001"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                flow.money(value)
        self.assertEqual(flow.money("1.005"), 101)

    def test_generated_report_escapes_untrusted_product_names(self):
        self.run_csv("a,2026-10-01,Nile,<script>alert(1)</script>,1,10,4\n")
        report = (self.root / "reports/report.html").read_text()
        self.assertNotIn("<script>", report)
        self.assertIn("&lt;script&gt;", report)

    def test_readonly_console_queries_real_database(self):
        self.run_csv("a,2026-10-01,Nile,Good,1,10,4\n")
        columns, rows = databases.query("SQLite", str(self.db), "SELECT product, quantity FROM orders")
        self.assertEqual(columns, ["product", "quantity"])
        self.assertEqual(rows, [("Good", 1)])
        for sql in ["DELETE FROM orders", "SELECT * FROM orders; DROP TABLE orders", "ATTACH DATABASE 'x' AS x"]:
            with self.assertRaises(ValueError):
                databases.query("SQLite", str(self.db), sql)

    def test_agents_receive_only_aggregate_data(self):
        report = self.run_csv("a,2026-10-01,PrivateCustomer,PrivateProduct,1,10,4\n")
        prompts = []
        def generate(model, role, prompt):
            prompts.append(prompt)
            return "Reviewed the supplied data"
        notes = agents.analyze(report, generate=generate)
        self.assertEqual([n["agent"] for n in notes], ["analyst", "operations", "reviewer"])
        self.assertNotIn("PrivateCustomer", "".join(prompts))
        self.assertNotIn("PrivateProduct", "".join(prompts))
        self.assertIn("Reviewed the supplied data", prompts[-1])

    def test_bundled_demo_expected_totals(self):
        demo = Path(__file__).resolve().parents[1] / "data/demo-sales.csv"
        result = flow.run(demo, self.db, self.root / "reports")
        self.assertEqual(result["kpis"]["orders"], 8)
        self.assertEqual(result["kpis"]["revenue"], 39100)
        self.assertEqual(result["kpis"]["profit"], 22100)
        self.assertEqual(json.loads((self.root / "reports/report.json").read_text()), result)


if __name__ == "__main__":
    unittest.main()
