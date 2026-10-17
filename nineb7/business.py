"""Institutional records for Studio. Independent of Qt and of Flow's demo data."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import sqlite3
import uuid

VERSION = 1
APPLICATION_ID = 0x39423753
CURRENCIES = ("EGP", "USD", "EUR", "SAR", "AED", "GBP")


class BusinessError(ValueError):
    """Stable message key translated by the UI."""


def money(value) -> int:
    try:
        d = Decimal(str(value))
        if not d.is_finite() or d < 0 or d > Decimal("999999999.99") or d != d.quantize(Decimal("0.01")):
            raise BusinessError("invalid_money")
        return int(d * 100)
    except (InvalidOperation, TypeError):
        raise BusinessError("invalid_money") from None


def required(value: str) -> str:
    value = str(value).strip()
    if not value or len(value) > 500:
        raise BusinessError("required_field")
    return value


def database_path() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    return base / "9b7/studio/organization.sqlite3"


class BusinessStore:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path is not None else database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(self.path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=10000")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        app_id = self.db.execute("PRAGMA application_id").fetchone()[0]
        tables = self.db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        if version > VERSION or (tables and app_id != APPLICATION_ID):
            self.db.close()
            raise BusinessError("incompatible_database")
        if version < VERSION:
            if tables:
                self.backup(self.path.with_name(self.path.name + ".pre-migration-" + uuid.uuid4().hex + ".sqlite3"))
            self._migrate()
        os.chmod(self.path, 0o600)

    def _migrate(self):
        self.db.executescript(f"""
        BEGIN IMMEDIATE;
        CREATE TABLE organization(id INTEGER PRIMARY KEY CHECK(id=1), name TEXT NOT NULL,
          industry TEXT NOT NULL, currency TEXT NOT NULL, language TEXT NOT NULL CHECK(language IN ('ar','en')));
        CREATE TABLE customers(id TEXT PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '',
          email TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '');
        CREATE TABLE products(id TEXT PRIMARY KEY, sku TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
          price_minor INTEGER NOT NULL CHECK(price_minor>=0), stock INTEGER NOT NULL CHECK(stock>=0));
        CREATE TABLE invoices(id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL REFERENCES customers(id),
          created_at TEXT NOT NULL, total_minor INTEGER NOT NULL CHECK(total_minor>=0));
        CREATE TABLE invoice_lines(invoice_id INTEGER NOT NULL REFERENCES invoices(id),
          product_id TEXT NOT NULL REFERENCES products(id), description TEXT NOT NULL,
          quantity INTEGER NOT NULL CHECK(quantity>0), price_minor INTEGER NOT NULL CHECK(price_minor>=0),
          PRIMARY KEY(invoice_id,product_id));
        CREATE TABLE stock_movements(id INTEGER PRIMARY KEY, product_id TEXT NOT NULL REFERENCES products(id),
          delta INTEGER NOT NULL, reason TEXT NOT NULL, invoice_id INTEGER REFERENCES invoices(id), created_at TEXT NOT NULL);
        CREATE TABLE audit(id INTEGER PRIMARY KEY, created_at TEXT NOT NULL, action TEXT NOT NULL,
          entity TEXT NOT NULL, record_id TEXT NOT NULL, details TEXT NOT NULL);
        PRAGMA application_id={APPLICATION_ID};
        PRAGMA user_version={VERSION};
        COMMIT;
        """)

    def close(self):
        self.db.close()

    def _audit(self, action, entity, record_id, details):
        self.db.execute("INSERT INTO audit(created_at,action,entity,record_id,details) VALUES(?,?,?,?,?)",
                        (datetime.now(timezone.utc).isoformat(), action, entity, str(record_id),
                         json.dumps(details, ensure_ascii=False)))

    def organization(self):
        row = self.db.execute("SELECT * FROM organization WHERE id=1").fetchone()
        return dict(row) if row else None

    def save_organization(self, name, industry, currency, language):
        name, industry = required(name), required(industry)
        if currency not in CURRENCIES or language not in ("ar", "en"):
            raise BusinessError("invalid_settings")
        old = self.organization()
        if old and old["currency"] != currency and self.db.execute("SELECT 1 FROM invoices LIMIT 1").fetchone():
            raise BusinessError("currency_locked")
        with self.db:
            self.db.execute("INSERT INTO organization VALUES(1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                            "name=excluded.name,industry=excluded.industry,currency=excluded.currency,language=excluded.language",
                            (name, industry, currency, language))
            self._audit("update" if old else "create", "organization", 1, {"before": old, "after": self.organization()})

    def save_customer(self, name, phone="", email="", notes="", record_id=None):
        name = required(name)
        record_id = record_id or uuid.uuid4().hex
        with self.db:
            self.db.execute("INSERT INTO customers VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                            "name=excluded.name,phone=excluded.phone,email=excluded.email,notes=excluded.notes",
                            (record_id, name, str(phone).strip(), str(email).strip(), str(notes).strip()))
            self._audit("save", "customer", record_id, {"name": name})
        return record_id

    def save_product(self, sku, name, price, stock=0, record_id=None):
        sku, name, price_minor = required(sku), required(name), money(price)
        if isinstance(stock, bool) or not isinstance(stock, int) or stock < 0 or stock > 10**9:
            raise BusinessError("invalid_quantity")
        record_id = record_id or uuid.uuid4().hex
        try:
            with self.db:
                self.db.execute("BEGIN IMMEDIATE")
                old = self.db.execute("SELECT stock FROM products WHERE id=?", (record_id,)).fetchone()
                self.db.execute("INSERT INTO products VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                                "sku=excluded.sku,name=excluded.name,price_minor=excluded.price_minor,stock=excluded.stock",
                                (record_id, sku, name, price_minor, stock))
                delta = stock - (old[0] if old else 0)
                if delta:
                    self.db.execute("INSERT INTO stock_movements(product_id,delta,reason,created_at) VALUES(?,?,?,?)",
                                    (record_id, delta, "adjustment", datetime.now(timezone.utc).isoformat()))
                self._audit("save", "product", record_id, {"sku": sku, "stock_delta": delta, "price_minor": price_minor})
        except sqlite3.IntegrityError:
            raise BusinessError("duplicate_sku") from None
        return record_id

    def records(self, entity, search=""):
        # The table name comes only from this fixed allowlist.
        if entity not in ("customers", "products"):
            raise BusinessError("invalid_entity")
        return [dict(row) for row in self.db.execute(
            f"SELECT * FROM {entity} WHERE instr(lower(name),lower(?))>0 ORDER BY name", (search,))]

    def post_invoice(self, customer_id, lines):
        """Atomically snapshot prices and decrement stock; posted invoices are immutable."""
        if not self.organization():
            raise BusinessError("organization_required")
        if not lines:
            raise BusinessError("empty_invoice")
        quantities = {}
        for product_id, qty in lines:
            if isinstance(qty, bool) or not isinstance(qty, int) or qty <= 0 or qty > 10**9:
                raise BusinessError("invalid_quantity")
            quantities[product_id] = quantities.get(product_id, 0) + qty
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if not self.db.execute("SELECT 1 FROM customers WHERE id=?", (customer_id,)).fetchone():
                raise BusinessError("customer_required")
            items, total = [], 0
            for product_id, qty in quantities.items():
                product = self.db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
                if not product or product["stock"] < qty:
                    raise BusinessError("insufficient_stock")
                total += product["price_minor"] * qty
                if total > 10**14:
                    raise BusinessError("invalid_money")
                items.append((product, qty))
            now = datetime.now(timezone.utc).isoformat()
            cursor = self.db.execute("INSERT INTO invoices(customer_id,created_at,total_minor) VALUES(?,?,?)", (customer_id, now, total))
            invoice_id = cursor.lastrowid
            for product, qty in items:
                self.db.execute("INSERT INTO invoice_lines VALUES(?,?,?,?,?)",
                                (invoice_id, product["id"], product["name"], qty, product["price_minor"]))
                self.db.execute("UPDATE products SET stock=stock-? WHERE id=?", (qty, product["id"]))
                self.db.execute("INSERT INTO stock_movements(product_id,delta,reason,invoice_id,created_at) VALUES(?,?,?,?,?)",
                                (product["id"], -qty, "sale", invoice_id, now))
            self._audit("post", "invoice", invoice_id, {"total_minor": total, "lines": len(items)})
        return invoice_id

    def invoices(self):
        return [dict(r) for r in self.db.execute("SELECT i.*,c.name AS customer FROM invoices i JOIN customers c ON c.id=i.customer_id ORDER BY i.id DESC")]

    def audit(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 500")]

    def dashboard(self):
        return {"customers": self.db.execute("SELECT count(*) FROM customers").fetchone()[0],
                "products": self.db.execute("SELECT count(*) FROM products").fetchone()[0],
                "invoices": self.db.execute("SELECT count(*) FROM invoices").fetchone()[0],
                "sales_minor": self.db.execute("SELECT coalesce(sum(total_minor),0) FROM invoices").fetchone()[0],
                "stock": self.db.execute("SELECT coalesce(sum(stock),0) FROM products").fetchone()[0]}

    def sales_by_product(self):
        return [tuple(r) for r in self.db.execute(
            "SELECT description,SUM(quantity*price_minor) FROM invoice_lines GROUP BY product_id ORDER BY 2 DESC LIMIT 8")]

    def backup(self, destination):
        destination = Path(destination)
        if destination.exists():
            raise BusinessError("file_exists")
        fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with sqlite3.connect(destination) as target:
            self.db.backup(target)
        return destination

    def restore(self, source):
        source = Path(source).resolve()
        if source == self.path.resolve():
            raise BusinessError("incompatible_database")
        try:
            incoming = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)
            if (incoming.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
                    or incoming.execute("PRAGMA user_version").fetchone()[0] != VERSION
                    or incoming.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
                    or incoming.execute("PRAGMA foreign_key_check").fetchone()):
                raise BusinessError("incompatible_database")
            # Check required schema before replacing any data.
            incoming.execute("SELECT name,currency,language FROM organization")
            incoming.execute("SELECT price_minor,stock FROM products")
            incoming.execute("SELECT invoice_id,quantity FROM invoice_lines")
            saved = self.backup(self.path.with_name(self.path.name + ".before-restore-" + uuid.uuid4().hex + ".sqlite3"))
            incoming.backup(self.db)
            with self.db:
                self._audit("restore", "database", 1, {"previous_backup": saved.name})
            return saved
        except sqlite3.DatabaseError:
            raise BusinessError("incompatible_database") from None
        finally:
            if "incoming" in locals():
                incoming.close()
