from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Mission, MissionCompletion, MissionStatus, MissionType, PlayerStats


def repeat_days(mission: Mission) -> set[int]:
    if not mission.repeat_days:
        return set(range(7))
    return {int(day) for day in mission.repeat_days.split(",") if day}


def is_daily_scheduled(mission: Mission, scheduled_on: date) -> bool:
    return (
        mission.type == MissionType.DAILY
        and mission.start_date <= scheduled_on
        and scheduled_on.weekday() in repeat_days(mission)
    )


def recalculate_daily_streak(
    session: Session,
    player: PlayerStats,
    reference_date: date,
) -> None:
    daily_missions = list(
        session.scalars(
            select(Mission)
            .where(Mission.type == MissionType.DAILY)
            .where(Mission.status == MissionStatus.ACTIVE)
            .where(Mission.start_date <= reference_date)
            .order_by(Mission.start_date, Mission.id)
        )
    )
    if not daily_missions:
        player.current_streak = 0
        player.last_active_date = None
        return

    mission_ids = [mission.id for mission in daily_missions]
    end_at = datetime.combine(reference_date, time.max)
    completions = session.scalars(
        select(MissionCompletion)
        .where(MissionCompletion.mission_id.in_(mission_ids))
        .where(MissionCompletion.completed_at <= end_at)
    )
    completed_by_date: dict[date, set[int]] = defaultdict(set)
    for completion in completions:
        completed_by_date[completion.completed_at.date()].add(completion.mission_id)

    current_streak = 0
    last_successful_date: date | None = None
    scheduled_on = min(mission.start_date for mission in daily_missions)
    while scheduled_on <= reference_date:
        required_ids = {
            mission.id
            for mission in daily_missions
            if is_daily_scheduled(mission, scheduled_on)
        }
        if required_ids:
            completed_ids = completed_by_date[scheduled_on]
            if scheduled_on == reference_date:
                if required_ids.intersection(completed_ids):
                    current_streak += 1
                    last_successful_date = scheduled_on
            elif required_ids.issubset(completed_ids):
                current_streak += 1
                last_successful_date = scheduled_on
            else:
                current_streak = 0
                last_successful_date = None
        scheduled_on += timedelta(days=1)

    player.current_streak = current_streak
    player.best_streak = max(player.best_streak, current_streak)
    player.last_active_date = last_successful_date
