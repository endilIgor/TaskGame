from __future__ import annotations

import argparse
import gzip
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import pymysql
from pymysql.connections import Connection


def _connect() -> Connection:
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "db"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "taskgame"),
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ.get("MYSQL_DATABASE", "taskgame"),
        charset="utf8mb4",
        autocommit=False,
    )


def _quote_identifier(identifier: str) -> str:
    return f"`{identifier.replace('`', '``')}`"


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int | float | Decimal):
        return str(value)
    if isinstance(value, datetime):
        value = value.isoformat(sep=" ", timespec="seconds")
    elif isinstance(value, date):
        value = value.isoformat()
    if isinstance(value, bytes):
        return "0x" + value.hex()
    text = str(value)
    text = (
        text.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\0", "\\0")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\x1a", "\\Z")
    )
    return f"'{text}'"


def _base_tables(connection: Connection) -> list[str]:
    with connection.cursor() as cursor:
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        return [row[0] for row in cursor.fetchall()]


def dump_database(output_path: Path) -> None:
    connection = _connect()
    try:
        tables = _base_tables(connection)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(output_path, "wt", encoding="utf-8", newline="\n") as dump:
            dump.write("-- TaskGame MySQL backup\n")
            dump.write("SET FOREIGN_KEY_CHECKS=0;\n")
            for table in tables:
                quoted_table = _quote_identifier(table)
                with connection.cursor() as cursor:
                    cursor.execute(f"SHOW CREATE TABLE {quoted_table}")
                    create_sql = cursor.fetchone()[1]
                    dump.write(f"DROP TABLE IF EXISTS {quoted_table};\n")
                    dump.write(f"{create_sql};\n")
                    cursor.execute(f"SELECT * FROM {quoted_table}")
                    columns = [column[0] for column in cursor.description]
                    quoted_columns = ", ".join(_quote_identifier(column) for column in columns)
                    for row in cursor.fetchall():
                        values = ", ".join(_sql_literal(value) for value in row)
                        dump.write(f"INSERT INTO {quoted_table} ({quoted_columns}) VALUES ({values});\n")
            dump.write("SET FOREIGN_KEY_CHECKS=1;\n")
    finally:
        connection.close()


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    quote: str | None = None
    escaped = False
    for char in sql:
        buffer.append(char)
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote:
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char in {"'", '"', "`"}:
            quote = char
            continue
        if char == ";":
            statement = "".join(buffer).strip()
            if statement and not statement.startswith("--"):
                statements.append(statement[:-1].strip())
            buffer.clear()
    tail = "".join(buffer).strip()
    if tail and not tail.startswith("--"):
        statements.append(tail)
    return statements


def restore_database(input_path: Path) -> None:
    connection = _connect()
    try:
        with gzip.open(input_path, "rt", encoding="utf-8") as dump:
            sql = "\n".join(line for line in dump if not line.lstrip().startswith("--"))
        with connection.cursor() as cursor:
            for statement in _split_sql_statements(sql):
                cursor.execute(statement)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def backup_command() -> int:
    backup_root = Path(os.environ.get("BACKUP_DIR", "./backups")) / "mysql"
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_path = backup_root / f"taskgame-{stamp}.sql.gz"
    if output_path.exists():
        print(f"Backup already exists: {output_path}", file=sys.stderr)
        return 1

    with NamedTemporaryFile(
        dir=backup_root,
        prefix=f".taskgame-{stamp}.",
        suffix=".sql.gz",
        delete=False,
    ) as partial_file:
        partial_path = Path(partial_file.name)

    try:
        dump_database(partial_path)
        partial_path.replace(output_path)
    except Exception:
        partial_path.unlink(missing_ok=True)
        raise

    print(output_path)
    return 0


def restore_command(input_path: str) -> int:
    restore_database(Path(input_path))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m backend.app.services.mysql_dump")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("backup")
    restore_parser = subparsers.add_parser("restore")
    restore_parser.add_argument("path")
    args = parser.parse_args()
    if args.command == "backup":
        return backup_command()
    if args.command == "restore":
        return restore_command(args.path)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
