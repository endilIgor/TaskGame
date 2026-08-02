from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models import Mission, MissionCompletion, MissionStatus, MissionType, PlayerStats
from backend.app.schemas import MissionCreate, MissionProgressUpdate, MissionUpdate, minimum_campaign_target_date
from backend.app.services.badges import evaluate_badges
from backend.app.services.game_rules import apply_xp_bonus, base_rewards, streak_bonus_percent
from backend.app.services.streaks import is_daily_scheduled, recalculate_daily_streak


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
    statement = select(Mission).where(Mission.id == mission_id).where(Mission.deleted_at.is_(None))
    if for_update:
        statement = statement.with_for_update()
    return session.scalar(statement)


def _validate_long_term_target(
    mission_type: MissionType,
    start_date: date,
    target_date: date | None,
    progress_target: int | None,
) -> None:
    if mission_type != MissionType.LONG_TERM:
        return
    if progress_target is None:
        raise ValueError("progress_target is required for long_term missions")
    minimum_target = minimum_campaign_target_date(start_date)
    if target_date is None or target_date < minimum_target:
        raise ValueError("target_date must be at least 30 days after start_date for long_term missions")


def _completion_key(mission: Mission, completion_date: date) -> str:
    if mission.type == MissionType.DAILY:
        return completion_date.isoformat()
    if mission.type == MissionType.WEEKLY:
        iso_year, iso_week, _ = completion_date.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    return "long_term"


def _validate_completion_eligibility(mission: Mission, completion_date: date) -> None:
    if completion_date > date.today():
        raise ValueError("Missions cannot be completed in the future")
    if mission.status != MissionStatus.ACTIVE:
        raise ValueError("Only active missions can be completed")
    if mission.start_date > completion_date:
        raise ValueError("Mission has not started")
    if mission.type == MissionType.DAILY and not is_daily_scheduled(
        mission, completion_date
    ):
        raise ValueError("Daily mission is not scheduled for this day")
    if (
        mission.type == MissionType.LONG_TERM
        and (
            mission.progress_target is None
            or mission.progress_current < mission.progress_target
        )
    ):
        raise ValueError("Long-term mission progress target has not been reached")


def _award_completion(
    session: Session,
    mission: Mission,
    completion_date: date,
) -> MissionCompletion:
    _validate_completion_eligibility(mission, completion_date)
    completion_key = _completion_key(mission, completion_date)
    existing_completion = session.scalar(
        select(MissionCompletion)
        .where(MissionCompletion.mission_id == mission.id)
        .where(MissionCompletion.completion_key == completion_key)
    )
    if existing_completion is not None:
        return existing_completion

    completion = MissionCompletion(
        mission_id=mission.id,
        completion_key=completion_key,
        completed_at=datetime.combine(completion_date, datetime.now().time()),
        xp_awarded=0,
        gold_awarded=0,
        streak_bonus_percent=0,
    )
    session.add(completion)
    session.flush()

    player = get_player(session, for_update=True)
    recalculate_daily_streak(session, player, date.today())
    bonus_percent = streak_bonus_percent(player.current_streak)
    base_xp, gold = base_rewards(mission.difficulty)
    xp = apply_xp_bonus(base_xp, bonus_percent)
    completion.xp_awarded = xp
    completion.gold_awarded = gold
    completion.streak_bonus_percent = bonus_percent
    player.total_xp += xp
    player.gold += gold

    if mission.type == MissionType.LONG_TERM:
        mission.status = MissionStatus.COMPLETED
    evaluate_badges(session)
    return completion


def list_missions(session: Session, include_archived: bool = False) -> list[Mission]:
    statement = select(Mission).where(Mission.deleted_at.is_(None)).order_by(Mission.id)
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
    start_date = values.get("start_date", mission.start_date)
    target_date = values.get("target_date", mission.target_date)
    progress_target = values.get("progress_target", mission.progress_target)
    _validate_long_term_target(mission_type, start_date, target_date, progress_target)
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


def restore_mission(session: Session, mission_id: int) -> Mission | None:
    mission = _get_mission(session, mission_id)
    if mission is None:
        return None

    if mission.status == MissionStatus.ARCHIVED:
        mission.status = MissionStatus.ACTIVE
        session.commit()
        session.refresh(mission)
    return mission


def delete_mission(session: Session, mission_id: int) -> bool:
    mission = _get_mission(session, mission_id)
    if mission is None:
        return False

    mission.deleted_at = datetime.now()
    player = get_player(session)
    recalculate_daily_streak(session, player, date.today())
    session.commit()
    return True


def advance_mission_progress(
    session: Session,
    mission_id: int,
    amount: MissionProgressUpdate | int,
) -> Mission | None:
    mission = _get_mission(session, mission_id, for_update=True)
    if mission is None:
        return None

    progress_amount = amount.amount if isinstance(amount, MissionProgressUpdate) else amount
    if progress_amount <= 0:
        raise ValueError("progress amount must be positive")
    if mission.type != MissionType.LONG_TERM:
        raise ValueError("Progress can only be advanced for long-term missions")
    if mission.status != MissionStatus.ACTIVE:
        raise ValueError("Only active missions can advance progress")
    if mission.start_date > date.today():
        raise ValueError("Mission has not started")

    mission.progress_current += progress_amount
    if (
        mission.type == MissionType.LONG_TERM
        and mission.progress_target is not None
        and mission.progress_current >= mission.progress_target
    ):
        mission.progress_current = mission.progress_target
        _award_completion(session, mission, date.today())

    else:
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
    try:
        completion = _award_completion(session, mission, completion_date)
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
