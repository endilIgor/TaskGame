from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models import (
    Badge,
    EarnedBadge,
    Mission,
    MissionCompletion,
    MissionStatus,
    MissionType,
    PlayerStats,
)
from backend.app.schemas import (
    BadgeStatusRead,
    CategoryCompletionRead,
    DashboardRead,
    DashboardTodayRead,
    DashboardWeeklyRead,
    GoalRead,
    PlayerSummaryRead,
    WeeklyReportRead,
)
from backend.app.services.game_rules import level_from_total_xp
from backend.app.services.streaks import recalculate_daily_streak


def _monday(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _completion_bounds(week_start: date) -> tuple[datetime, datetime, date]:
    week_end = week_start + timedelta(days=6)
    return (
        datetime.combine(week_start, time.min),
        datetime.combine(week_end, time.max),
        week_end,
    )


def _repeat_days(mission: Mission) -> set[int]:
    if mission.repeat_days is None:
        return set(range(7))
    return {int(day) for day in mission.repeat_days.split(",") if day}


def _missions_failed(
    session: Session,
    week_start: date,
    week_end: date,
    reference_today: date,
    completion_dates: dict[int, set[date]],
) -> int:
    missions = session.scalars(
        select(Mission).where(
            Mission.status == MissionStatus.ACTIVE,
            Mission.type.in_((MissionType.DAILY, MissionType.WEEKLY)),
        )
    )
    failed = 0
    for mission in missions:
        if mission.start_date > week_end:
            continue
        if mission.type == MissionType.WEEKLY:
            if week_end < reference_today and not completion_dates[mission.id]:
                failed += 1
            continue

        last_completed_period = min(week_end, reference_today - timedelta(days=1))
        period_date = max(week_start, mission.start_date)
        repeat_days = _repeat_days(mission)
        while period_date <= last_completed_period:
            if (
                period_date.weekday() in repeat_days
                and period_date not in completion_dates[mission.id]
            ):
                failed += 1
            period_date += timedelta(days=1)
    return failed


def _build_weekly_report(
    session: Session,
    week_start: date,
    reference_today: date,
) -> WeeklyReportRead:
    week_start = _monday(week_start)
    start_at, end_at, week_end = _completion_bounds(week_start)
    completions = list(
        session.scalars(
            select(MissionCompletion)
            .where(MissionCompletion.completed_at >= start_at)
            .where(MissionCompletion.completed_at <= end_at)
            .order_by(MissionCompletion.completed_at)
        )
    )
    completion_dates: dict[int, set[date]] = defaultdict(set)
    completions_by_day: Counter[str] = Counter()
    daily_completions = [0] * 7
    for completion in completions:
        completion_dates[completion.mission_id].add(completion.completed_at.date())
        completions_by_day[completion.completed_at.strftime("%A")] += 1
        daily_completions[completion.completed_at.weekday()] += 1

    mission_ids = {completion.mission_id for completion in completions}
    missions_by_id = {
        mission.id: mission
        for mission in session.scalars(select(Mission).where(Mission.id.in_(mission_ids)))
    }
    category_counts: Counter[str] = Counter()
    goals_completed: list[str] = []
    for completion in completions:
        mission = missions_by_id.get(completion.mission_id)
        if mission is None:
            continue
        category_counts[mission.category or "Sem categoria"] += 1
        if mission.type == MissionType.LONG_TERM:
            goals_completed.append(mission.title)

    player = session.scalar(select(PlayerStats).limit(1))
    if player is not None:
        recalculate_daily_streak(session, player, reference_today)
    return WeeklyReportRead(
        week_start=week_start,
        week_end=week_end,
        missions_completed=len(completions),
        missions_failed=_missions_failed(
            session,
            week_start,
            week_end,
            reference_today,
            completion_dates,
        ),
        xp_gained=sum(completion.xp_awarded for completion in completions),
        gold_gained=sum(completion.gold_awarded for completion in completions),
        best_day=(
            max(completions_by_day, key=completions_by_day.get)
            if completions_by_day
            else None
        ),
        current_streak=player.current_streak if player else 0,
        best_streak=player.best_streak if player else 0,
        daily_completions=daily_completions,
        top_categories=[
            CategoryCompletionRead(category=category, completions=count)
            for category, count in sorted(
                category_counts.items(),
                key=lambda item: (-item[1], item[0].lower()),
            )[:5]
        ],
        goals_completed=goals_completed,
    )


def build_weekly_report(
    session: Session,
    week_start: date | None = None,
) -> WeeklyReportRead:
    reference_today = date.today()
    return _build_weekly_report(session, week_start or _monday(reference_today), reference_today)


def list_goals(session: Session) -> list[GoalRead]:
    missions = session.scalars(
        select(Mission)
        .where(Mission.type == MissionType.LONG_TERM)
        .where(Mission.status != MissionStatus.ARCHIVED)
        .order_by(Mission.id)
    )
    goals = []
    for mission in missions:
        progress_percent = min(
            100,
            int((mission.progress_current / mission.progress_target) * 100),
        )
        goals.append(
            GoalRead.model_validate(mission).model_copy(
                update={"progress_percent": progress_percent}
            )
        )
    return goals


def _recent_badge(session: Session) -> BadgeStatusRead | None:
    row = session.execute(
        select(Badge, EarnedBadge)
        .join(EarnedBadge, EarnedBadge.badge_id == Badge.id)
        .order_by(EarnedBadge.earned_at.desc(), EarnedBadge.id.desc())
        .limit(1)
    ).first()
    if row is None:
        return None
    badge, earned_badge = row
    return BadgeStatusRead(
        id=badge.id,
        code=badge.code,
        name=badge.name,
        description=badge.description,
        condition_type=badge.condition_type,
        threshold=badge.threshold,
        earned=True,
        earned_at=earned_badge.earned_at,
    )


def build_dashboard(session: Session, today: date | None = None) -> DashboardRead:
    effective_today = today or date.today()
    player = session.scalar(select(PlayerStats).limit(1))
    if player is not None:
        recalculate_daily_streak(session, player, effective_today)
    total_xp = player.total_xp if player else 0
    level, xp_into_level, xp_for_next_level = level_from_total_xp(total_xp)
    today_start = datetime.combine(effective_today, time.min)
    today_end = datetime.combine(effective_today, time.max)
    completed = session.scalar(
        select(func.count())
        .select_from(MissionCompletion)
        .where(MissionCompletion.completed_at >= today_start)
        .where(MissionCompletion.completed_at <= today_end)
    )
    active = session.scalar(
        select(func.count())
        .select_from(Mission)
        .where(Mission.status == MissionStatus.ACTIVE)
        .where(Mission.start_date <= effective_today)
    )
    overdue = session.scalar(
        select(func.count())
        .select_from(Mission)
        .where(Mission.status == MissionStatus.ACTIVE)
        .where(Mission.target_date.is_not(None))
        .where(Mission.target_date < effective_today)
    )
    upcoming_missions = list(
        session.scalars(
            select(Mission)
            .where(Mission.status == MissionStatus.ACTIVE)
            .order_by(Mission.target_date.is_(None), Mission.target_date, Mission.id)
        )
    )
    weekly_report = _build_weekly_report(
        session,
        _monday(effective_today),
        effective_today,
    )
    return DashboardRead(
        player=PlayerSummaryRead(
            total_xp=total_xp,
            gold=player.gold if player else 0,
            level=level,
            xp_into_level=xp_into_level,
            xp_for_next_level=xp_for_next_level,
            current_streak=player.current_streak if player else 0,
            best_streak=player.best_streak if player else 0,
        ),
        today=DashboardTodayRead(
            completed=completed or 0,
            active=active or 0,
            overdue=overdue or 0,
        ),
        weekly=DashboardWeeklyRead(
            missions_completed=weekly_report.missions_completed,
            xp_gained=weekly_report.xp_gained,
            gold_gained=weekly_report.gold_gained,
            best_day=weekly_report.best_day,
        ),
        upcoming_missions=upcoming_missions,
        recent_badge=_recent_badge(session),
    )
