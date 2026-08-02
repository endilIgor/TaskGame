import csv
import io
from datetime import date, datetime
from enum import Enum
from typing import Any

from sqlalchemy import select
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from backend.app.models import (
    Badge,
    EarnedBadge,
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
        "rewards": _model_rows(session, Reward),
        "reward_purchases": _model_rows(session, RewardPurchase),
        "weekly_snapshots": _model_rows(session, WeeklySnapshot),
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
    writer.writerows(rows)
    return output.getvalue()


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
