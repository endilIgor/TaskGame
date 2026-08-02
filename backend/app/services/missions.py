from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models import Mission, MissionCompletion, MissionStatus, MissionType, PlayerStats
from backend.app.schemas import MissionCreate, MissionProgressUpdate, MissionUpdate
from backend.app.services.badges import evaluate_badges
from backend.app.services.game_rules import apply_xp_bonus, base_rewards, streak_bonus_percent


def get_player(session: Session, for_update: bool = False) -> PlayerStats:
    statement = select(PlayerStats).limit(1)
    if for_update:
        statement = statement.with_for_update()
    player = session.scalar(statement)
    if player is None:
        player = PlayerStats(total_xp=0, gold=0, current_streak=0, best_streak=0)
        session.add(player)
        session.flush()
    return player


def _repeat_days_value(repeat_days: list[int] | None) -> str | None:
    if repeat_days is None:
        return None
    return ",".join(str(day) for day in repeat_days)


def _get_mission(
    session: Session,
    mission_id: int,
    for_update: bool = False,
) -> Mission | None:
    if not for_update:
        return session.get(Mission, mission_id)
    return session.scalar(select(Mission).where(Mission.id == mission_id).with_for_update())


def _completion_key(mission: Mission, completion_date: date) -> str:
    if mission.type in (MissionType.DAILY, MissionType.WEEKLY):
        return completion_date.isoformat()
    return "long_term"


def list_missions(session: Session, include_archived: bool = False) -> list[Mission]:
    statement = select(Mission).order_by(Mission.id)
    if not include_archived:
        statement = statement.where(Mission.status != MissionStatus.ARCHIVED)
    return list(session.scalars(statement))


def create_mission(session: Session, data: MissionCreate) -> Mission:
    values = data.model_dump()
    values["repeat_days"] = _repeat_days_value(values["repeat_days"])
    mission = Mission(**values)
    session.add(mission)
    session.commit()
    session.refresh(mission)
    return mission


def update_mission(session: Session, mission_id: int, data: MissionUpdate) -> Mission | None:
    mission = _get_mission(session, mission_id)
    if mission is None:
        return None

    values = data.model_dump(exclude_unset=True)
    mission_type = values.get("type", mission.type)
    progress_target = values.get("progress_target", mission.progress_target)
    if mission_type == MissionType.LONG_TERM and progress_target is None:
        raise ValueError("progress_target is required for long_term missions")
    if "repeat_days" in values:
        values["repeat_days"] = _repeat_days_value(values["repeat_days"])
    for field, value in values.items():
        setattr(mission, field, value)

    session.commit()
    session.refresh(mission)
    return mission


def archive_mission(session: Session, mission_id: int) -> Mission | None:
    mission = _get_mission(session, mission_id)
    if mission is None:
        return None

    mission.status = MissionStatus.ARCHIVED
    session.commit()
    session.refresh(mission)
    return mission


def advance_mission_progress(
    session: Session,
    mission_id: int,
    amount: MissionProgressUpdate | int,
) -> Mission | None:
    mission = _get_mission(session, mission_id)
    if mission is None:
        return None

    progress_amount = amount.amount if isinstance(amount, MissionProgressUpdate) else amount
    if progress_amount <= 0:
        raise ValueError("progress amount must be positive")

    mission.progress_current += progress_amount
    if (
        mission.type == MissionType.LONG_TERM
        and mission.progress_target is not None
        and mission.progress_current >= mission.progress_target
    ):
        mission.status = MissionStatus.COMPLETED

    evaluate_badges(session)
    session.commit()
    session.refresh(mission)
    return mission


def complete_mission(
    session: Session,
    mission_id: int,
    completed_on: date | None = None,
) -> MissionCompletion | None:
    mission = _get_mission(session, mission_id, for_update=True)
    if mission is None:
        return None

    mission_id = mission.id
    completion_date = completed_on or date.today()
    completion_key = _completion_key(mission, completion_date)
    existing_completion = session.scalar(
        select(MissionCompletion)
        .where(MissionCompletion.mission_id == mission_id)
        .where(MissionCompletion.completion_key == completion_key)
    )
    if existing_completion is not None:
        return existing_completion

    player = get_player(session, for_update=True)
    if player.last_active_date == completion_date - timedelta(days=1):
        player.current_streak += 1
    elif player.last_active_date != completion_date:
        player.current_streak = 1
    player.last_active_date = completion_date
    player.best_streak = max(player.best_streak, player.current_streak)

    bonus_percent = streak_bonus_percent(player.current_streak)
    base_xp, gold = base_rewards(mission.difficulty)
    xp = apply_xp_bonus(base_xp, bonus_percent)
    player.total_xp += xp
    player.gold += gold

    completion = MissionCompletion(
        mission_id=mission_id,
        completion_key=completion_key,
        completed_at=datetime.combine(completion_date, datetime.now().time()),
        xp_awarded=xp,
        gold_awarded=gold,
        streak_bonus_percent=bonus_percent,
    )
    session.add(completion)
    if mission.type == MissionType.LONG_TERM:
        mission.status = MissionStatus.COMPLETED
    try:
        evaluate_badges(session)
        session.commit()
    except IntegrityError:
        session.rollback()
        existing_completion = session.scalar(
            select(MissionCompletion)
            .where(MissionCompletion.mission_id == mission_id)
            .where(MissionCompletion.completion_key == completion_key)
        )
        if existing_completion is not None:
            return existing_completion
        raise
    session.refresh(completion)
    return completion
