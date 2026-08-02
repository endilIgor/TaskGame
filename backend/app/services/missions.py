from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Mission, MissionCompletion, MissionStatus, MissionType, PlayerStats
from backend.app.schemas import MissionCreate, MissionProgressUpdate, MissionUpdate
from backend.app.services.game_rules import apply_xp_bonus, base_rewards, streak_bonus_percent


def get_player(session: Session) -> PlayerStats:
    player = session.scalar(select(PlayerStats).limit(1))
    if player is None:
        player = PlayerStats(total_xp=0, gold=0, current_streak=0, best_streak=0)
        session.add(player)
        session.flush()
    return player


def _repeat_days_value(repeat_days: list[int] | None) -> str | None:
    if repeat_days is None:
        return None
    return ",".join(str(day) for day in repeat_days)


def _get_mission(session: Session, mission_id: int) -> Mission | None:
    return session.get(Mission, mission_id)


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

    session.commit()
    session.refresh(mission)
    return mission


def complete_mission(
    session: Session,
    mission_id: int,
    completed_on: date | None = None,
) -> MissionCompletion | None:
    mission = _get_mission(session, mission_id)
    if mission is None:
        return None

    completion_date = completed_on or date.today()
    if mission.type in (MissionType.DAILY, MissionType.WEEKLY):
        start = datetime.combine(completion_date, time.min)
        end = start + timedelta(days=1)
        existing_completion = session.scalar(
            select(MissionCompletion)
            .where(MissionCompletion.mission_id == mission.id)
            .where(MissionCompletion.completed_at >= start)
            .where(MissionCompletion.completed_at < end)
        )
        if existing_completion is not None:
            return existing_completion
    else:
        existing_completion = session.scalar(
            select(MissionCompletion).where(MissionCompletion.mission_id == mission.id)
        )
        if existing_completion is not None:
            return existing_completion

    player = get_player(session)
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
        mission_id=mission.id,
        completed_at=datetime.combine(completion_date, datetime.now().time()),
        xp_awarded=xp,
        gold_awarded=gold,
        streak_bonus_percent=bonus_percent,
    )
    session.add(completion)
    if mission.type == MissionType.LONG_TERM:
        mission.status = MissionStatus.COMPLETED
    session.commit()
    session.refresh(completion)
    return completion
