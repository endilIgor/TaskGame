from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.app.models import (
    Badge,
    Difficulty,
    EarnedBadge,
    HeroClass,
    Mission,
    MissionCompletion,
    MissionStatus,
    MissionType,
    PlayerProfile,
    PlayerStats,
    RewardPurchase,
)
from backend.app.schemas import BadgeStatusRead
from backend.app.services.reports import build_weekly_report


def _has_rows(session: Session, statement: Select[tuple[int]]) -> bool:
    return session.scalar(statement.limit(1)) is not None


def _mission_completion_count(
    session: Session,
    *,
    mission_type: MissionType | None = None,
    difficulty: Difficulty | None = None,
) -> int:
    statement = select(func.count()).select_from(MissionCompletion).join(Mission)
    if mission_type is not None:
        statement = statement.where(Mission.type == mission_type)
    if difficulty is not None:
        statement = statement.where(Mission.difficulty == difficulty)
    return session.scalar(statement) or 0


def evaluate_badges(session: Session) -> list[EarnedBadge]:
    player = session.scalar(select(PlayerStats).limit(1))
    current_streak = player.current_streak if player else 0
    total_xp = player.total_xp if player else 0
    weekly_report = build_weekly_report(session)
    profile = session.scalar(select(PlayerProfile).limit(1))
    onboarding_completed = profile is not None and profile.onboarding_completed_at is not None
    conditions = {
        f"class_{hero_class.value}": (
            onboarding_completed and profile is not None and profile.hero_class == hero_class
        )
        for hero_class in HeroClass
    }
    conditions.update({
        "streak_7": current_streak >= 7,
        "streak_30": current_streak >= 30,
        "missions_100": session.scalar(select(func.count()).select_from(MissionCompletion)) >= 100,
        "daily_contracts_10": _mission_completion_count(session, mission_type=MissionType.DAILY) >= 10,
        "weekly_contracts_4": _mission_completion_count(session, mission_type=MissionType.WEEKLY) >= 4,
        "epic_campaigns_3": _mission_completion_count(session, difficulty=Difficulty.EPIC) >= 3,
        "first_goal": _has_rows(
            session,
            select(Mission.id).where(
                Mission.type == MissionType.LONG_TERM,
                Mission.status == MissionStatus.COMPLETED,
            ),
        ),
        "first_reward": _has_rows(session, select(RewardPurchase.id)),
        "xp_1000": total_xp >= 1000,
        "xp_10000": total_xp >= 10000,
        "perfect_week": (
            weekly_report.missions_failed == 0
            and weekly_report.missions_completed >= 7
        ),
    })
    badges = list(session.scalars(select(Badge).where(Badge.code.in_(conditions))).all())
    earned_badge_ids = set(
        session.scalars(
            select(EarnedBadge.badge_id).where(
                EarnedBadge.badge_id.in_(badge.id for badge in badges)
            )
        ).all()
    )
    unlocked = [
        EarnedBadge(badge_id=badge.id)
        for badge in badges
        if conditions[badge.code] and badge.id not in earned_badge_ids
    ]
    session.add_all(unlocked)
    return unlocked


def list_badges_with_status(session: Session) -> list[BadgeStatusRead]:
    rows = session.execute(
        select(Badge, EarnedBadge)
        .outerjoin(EarnedBadge, EarnedBadge.badge_id == Badge.id)
        .order_by(Badge.id)
    )
    return [
        BadgeStatusRead(
            id=badge.id,
            code=badge.code,
            name=badge.name,
            description=badge.description,
            condition_type=badge.condition_type,
            threshold=badge.threshold,
            earned=earned_badge is not None,
            earned_at=earned_badge.earned_at if earned_badge else None,
        )
        for badge, earned_badge in rows
    ]
