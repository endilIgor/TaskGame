import csv
import io
import unicodedata
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from backend.app.models import (
    Badge,
    EarnedBadge,
    JournalEntry,
    Mission,
    MissionCompletion,
    PlayerStats,
    Reward,
    RewardPurchase,
    WeeklySnapshot,
)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def _model_rows(session: Session, model: type[Any]) -> list[dict[str, object]]:
    columns = [column.key for column in inspect(model).columns]
    records = session.scalars(select(model).order_by(model.id)).all()
    return [
        {column: _serialize_value(getattr(record, column)) for column in columns}
        for record in records
    ]


def export_all_json(session: Session) -> dict[str, object]:
    return {
        "missions": _model_rows(session, Mission),
        "mission_completions": _model_rows(session, MissionCompletion),
        "player_stats": _model_rows(session, PlayerStats),
        "badges": _model_rows(session, Badge),
        "earned_badges": _model_rows(session, EarnedBadge),
        "journal_entries": _model_rows(session, JournalEntry),
        "rewards": _model_rows(session, Reward),
        "reward_purchases": _model_rows(session, RewardPurchase),
        "weekly_snapshots": _model_rows(session, WeeklySnapshot),
    }


def mysql_dump_status(backup_dir: str) -> dict[str, object | None]:
    dumps = list((Path(backup_dir) / "mysql").glob("taskgame-*.sql.gz"))
    if not dumps:
        return {
            "last_mysql_dump_at": None,
            "last_mysql_dump_filename": None,
        }
    latest = max(dumps, key=lambda path: (path.stat().st_mtime, path.name))
    return {
        "last_mysql_dump_at": datetime.fromtimestamp(latest.stat().st_mtime),
        "last_mysql_dump_filename": latest.name,
    }


def _csv_export(rows: list[dict[str, object]], columns: list[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=columns,
        lineterminator="\n",
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(
        {
            column: _escape_csv_formula(row.get(column))
            for column in columns
        }
        for row in rows
    )
    return output.getvalue()


def _escape_csv_formula(value: object) -> object:
    if isinstance(value, str):
        first_content = 0
        while first_content < len(value) and (
            value[first_content].isspace()
            or unicodedata.category(value[first_content]).startswith("C")
        ):
            first_content += 1
        if first_content < len(value) and value[first_content] in "=+-@":
            return f"'{value}"
    return value


def missions_csv(session: Session) -> str:
    columns = ["id", "title", "type", "difficulty", "status"]
    rows = _model_rows(session, Mission)
    return _csv_export(rows, columns)


def completions_csv(session: Session) -> str:
    columns = [
        "id",
        "mission_id",
        "completion_key",
        "completed_at",
        "xp_awarded",
        "gold_awarded",
        "streak_bonus_percent",
        "note",
    ]
    rows = _model_rows(session, MissionCompletion)
    return _csv_export(rows, columns)
