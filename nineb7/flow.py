"""Transactional CSV -> SQLite -> KPI report workflow, without cloud dependencies."""
from __future__ import annotations

import argparse
import csv
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import html
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import uuid

REQUIRED = {"order_id", "date", "customer", "product", "quantity", "unit_price", "unit_cost"}
MAX_CSV_BYTES = 25 * 1024 * 1024


def state_dir() -> Path:
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "9b7"


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.execute("PRAGMA foreign_keys=ON")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY, started_at TEXT NOT NULL, source_sha256 TEXT NOT NULL,
            inserted INTEGER NOT NULL, duplicates INTEGER NOT NULL, rejected INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY, date TEXT NOT NULL, customer TEXT NOT NULL,
            product TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>0),
            price_cents INTEGER NOT NULL CHECK(price_cents>=0),
            cost_cents INTEGER NOT NULL CHECK(cost_cents>=0),
            run_id TEXT NOT NULL REFERENCES runs(id));
        CREATE TABLE IF NOT EXISTS rejections (
            run_id TEXT NOT NULL REFERENCES runs(id), line INTEGER NOT NULL, reason TEXT NOT NULL);
    """)
    return db


def money(value: str) -> int:
    try:
        number = Decimal(value.strip())
        if not number.is_finite() or number < 0 or number > Decimal("1000000000"):
            raise ValueError("money must be finite, nonnegative, and <= 1 billion")
        return int((number * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError("invalid monetary value") from exc


def validated(row: dict) -> tuple:
    values = {}
    for field in REQUIRED:
        val = row.get(field)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"missing {field}")
        values[field] = val.strip()
    if any(len(values[key]) > 200 for key in ("order_id", "customer", "product")):
        raise ValueError("identifier or label exceeds 200 characters")
    date.fromisoformat(values["date"])
    quantity = int(values["quantity"])
    if not 0 < quantity <= 1_000_000:
        raise ValueError("quantity must be 1..1000000")
    return (values["order_id"], values["date"], values["customer"], values["product"],
            quantity, money(values["unit_price"]), money(values["unit_cost"]))


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".9b7-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def metrics(db: sqlite3.Connection) -> dict:
    count, revenue, cost = db.execute(
        "SELECT count(*), coalesce(sum(quantity*price_cents),0), "
        "coalesce(sum(quantity*cost_cents),0) FROM orders"
    ).fetchone()
    products = [{"product": row[0], "units": row[1], "revenue": row[2] / 100}
                for row in db.execute("SELECT product,sum(quantity),sum(quantity*price_cents) "
                                      "FROM orders GROUP BY product ORDER BY 3 DESC LIMIT 10")]
    return {"orders": count, "revenue": revenue / 100, "cost": cost / 100,
            "profit": (revenue - cost) / 100,
            "margin_percent": round((revenue - cost) / revenue * 100, 2) if revenue else 0,
            "top_products": products}


def run(csv_path: Path, database: Path, output: Path, strict: bool = False) -> dict:
    raw = csv_path.read_bytes()
    if len(raw) > MAX_CSV_BYTES:
        raise ValueError("CSV exceeds the 25 MiB import limit")
    # Parse the exact bytes we hash; reject malformed headers before changing data.
    import io
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    if not reader.fieldnames or not REQUIRED.issubset(reader.fieldnames):
        raise ValueError("CSV requires: " + ", ".join(sorted(REQUIRED)))
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("duplicate CSV column names")
    rows, rejected = [], []
    for line, row in enumerate(reader, 2):
        try:
            if None in row:
                raise ValueError("too many columns")
            rows.append((line, validated(row)))
        except (ValueError, TypeError) as exc:
            rejected.append({"line": line, "reason": str(exc)})
    if strict and rejected:
        raise ValueError(f"strict import rejected {len(rejected)} row(s); nothing imported")
    run_id = uuid.uuid4().hex
    summary = {"run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat(),
               "source_sha256": hashlib.sha256(raw).hexdigest(), "inserted": 0,
               "duplicates": 0, "rejected": len(rejected), "errors": rejected}
    db = connect(database)
    try:
        with db:
            db.execute("INSERT INTO runs VALUES (?,?,?,?,?,?)", (
                run_id, summary["started_at"], summary["source_sha256"], 0, 0, 0))
            for line, row in rows:
                existing = db.execute("SELECT order_id,date,customer,product,quantity,price_cents,cost_cents "
                                      "FROM orders WHERE order_id=?", (row[0],)).fetchone()
                if existing is not None:
                    if existing == row:
                        summary["duplicates"] += 1
                    else:
                        if strict:
                            raise ValueError(f"conflicting order_id on line {line}; transaction rolled back")
                        rejected.append({"line": line, "reason": "order_id already exists with different data"})
                        summary["rejected"] += 1
                else:
                    db.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)", (*row, run_id))
                    summary["inserted"] += 1
            db.executemany("INSERT INTO rejections VALUES (?,?,?)",
                           [(run_id, item["line"], item["reason"]) for item in rejected])
            db.execute("UPDATE runs SET inserted=?,duplicates=?,rejected=? WHERE id=?",
                       (summary["inserted"], summary["duplicates"], summary["rejected"], run_id))
            summary["kpis"] = metrics(db)
    finally:
        db.close()
    # Reports can be regenerated with the report command if a disk error occurs after commit.
    write_report(summary, output)
    return summary


def write_report(summary: dict, output: Path) -> None:
    atomic_write(output / "report.json", json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    kpis = summary["kpis"]
    cards = "".join(f'<article><small>{html.escape(key.replace("_", " "))}</small><h2>{value}</h2></article>'
                    for key, value in kpis.items() if key != "top_products")
    rows = "".join(f'<tr><td>{html.escape(p["product"])}</td><td>{p["units"]}</td>'
                   f'<td>{p["revenue"]:.2f}</td></tr>' for p in kpis["top_products"])
    document = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>9b7 business report</title>
<style>body{{background:#101820;color:#e5f3f0;font:16px system-ui;margin:5vw}}h1{{color:#6ce5ba}}
.cards{{display:flex;gap:16px;flex-wrap:wrap}}article{{background:#1b2935;padding:24px;min-width:120px;border-radius:16px}}
table{{border-collapse:collapse;width:100%;margin-top:30px}}td,th{{padding:14px;text-align:left;border-bottom:1px solid #304451}}
small{{color:#a2b8bf}}code{{overflow-wrap:anywhere}}</style>
<h1>9b7 / Business pulse</h1><p>Validated sales data · amounts use the dataset's currency</p>
<div class="cards">{cards}</div><table><tr><th>Product</th><th>Units</th><th>Revenue</th></tr>{rows}</table>
<p>Run <code>{html.escape(str(summary.get("run_id", "snapshot")))}</code></p>
<p>Imported: {summary.get("inserted", 0)} · duplicates: {summary.get("duplicates", 0)} · rejected: {summary.get("rejected", 0)}</p>
<p>9b7 Flow · auditable local automation</p></html>'''
    atomic_write(output / "report.html", document)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "report", "history"):
        p = sub.add_parser(command)
        p.add_argument("--database", type=Path, default=state_dir() / "business.sqlite3")
        if command != "history":
            p.add_argument("--output", type=Path, default=state_dir() / "reports")
        if command == "run":
            p.add_argument("csv", type=Path)
            p.add_argument("--strict", action="store_true", help="roll back on any invalid or conflicting row")
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            result = run(args.csv, args.database, args.output, args.strict)
        else:
            db = connect(args.database)
            try:
                if args.command == "history":
                    db.row_factory = sqlite3.Row
                    result = [dict(row) for row in db.execute("SELECT * FROM runs ORDER BY started_at DESC LIMIT 50")]
                else:
                    result = {"kpis": metrics(db)}
                    write_report(result, args.output)
            finally:
                db.close()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2 if isinstance(result, dict) and result.get("rejected") else 0
    except (OSError, UnicodeError, ValueError, sqlite3.Error) as exc:
        parser.exit(1, f"9b7 Flow: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
