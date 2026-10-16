"""One read-only console for six common BIS database families."""
from __future__ import annotations
import json
from pathlib import Path
import re
import sqlite3
from urllib.parse import unquote, urlsplit

ENGINES = ("SQLite", "PostgreSQL", "MySQL/MariaDB", "Cassandra", "MongoDB", "Redis")
LIMIT = 200


def select_only(query: str) -> str:
    value = query.strip().rstrip(";").strip()
    if not re.match(r"^SELECT\s", value, re.IGNORECASE) or ";" in value:
        raise ValueError("This console accepts a single SELECT query. Use native admin tools for writes.")
    return value


def query(engine: str, connection: str, statement: str) -> tuple[list, list]:
    if engine not in ENGINES:
        raise ValueError("unsupported database engine")
    if engine == "SQLite":
        uri = Path(connection).expanduser().resolve().as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=5) as db:
            db.execute("PRAGMA query_only=ON")
            import time
            deadline = time.monotonic() + 10
            db.set_progress_handler(lambda: time.monotonic() > deadline, 1000)
            cursor = db.execute(select_only(statement))
            return [c[0] for c in cursor.description], cursor.fetchmany(LIMIT)
    if engine == "PostgreSQL":
        import psycopg
        with psycopg.connect(connection, connect_timeout=8,
                             options="-c default_transaction_read_only=on -c statement_timeout=10000") as db:
            cursor = db.execute(select_only(statement))
            return [c.name for c in cursor.description], cursor.fetchmany(LIMIT)
    uri = urlsplit(connection)
    if engine == "MySQL/MariaDB":
        import pymysql
        db = pymysql.connect(host=uri.hostname or "localhost", port=uri.port or 3306,
                             user=unquote(uri.username or ""), password=unquote(uri.password or ""),
                             database=uri.path.lstrip("/"), connect_timeout=8, read_timeout=10)
        try:
            with db.cursor() as cursor:
                cursor.execute("START TRANSACTION READ ONLY")
                cursor.execute(select_only(statement))
                return [c[0] for c in cursor.description], cursor.fetchmany(LIMIT)
        finally:
            db.rollback()
            db.close()
    if engine == "Cassandra":
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider
        auth = PlainTextAuthProvider(unquote(uri.username), unquote(uri.password or "")) if uri.username else None
        cluster = Cluster([uri.hostname or "localhost"], port=uri.port or 9042,
                          auth_provider=auth, connect_timeout=8)
        try:
            session = cluster.connect(uri.path.lstrip("/") or None)
            session.default_timeout = 10
            session.default_fetch_size = LIMIT
            result = session.execute(select_only(statement))
            # Do not auto-fetch additional pages on large tables.
            return list(result.column_names), list(result.current_rows)[:LIMIT]
        finally:
            cluster.shutdown()
    if engine == "MongoDB":
        from pymongo import MongoClient
        request = json.loads(statement)
        if set(request) - {"collection", "filter"} or not isinstance(request.get("filter", {}), dict):
            raise ValueError('Use {"collection":"sales","filter":{}}')
        with MongoClient(connection, serverSelectionTimeoutMS=8000) as client:
            documents = list(client.get_default_database()[request["collection"]]
                             .find(request.get("filter", {})).max_time_ms(10000).limit(LIMIT))
            return ["document"], [[json.dumps(d, default=str, ensure_ascii=False)] for d in documents]
    import redis
    client = redis.Redis.from_url(connection, socket_timeout=8, decode_responses=True)
    try:
        request = json.loads(statement)
        if set(request) == {"get"}:
            return ["key", "value"], [[request["get"], client.get(request["get"])]]
        if set(request) == {"scan"}:
            _, keys = client.scan(0, match=request["scan"], count=LIMIT)
            return ["key"], [[k] for k in keys[:LIMIT]]
        raise ValueError('Use {"get":"key"} or {"scan":"pattern*"}')
    finally:
        client.close()
