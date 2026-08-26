from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from backend.app.models import Badge, EarnedBadge, Mission, MissionStatus, Reward, RewardPurchase, RewardStatus
from backend.app.schemas import RewardCreate, RewardSuggestionRead, RewardUpdate
from backend.app.services.badges import evaluate_badges
from backend.app.services.missions import get_player


def _get_reward(session: Session, reward_id: int, for_update: bool = False) -> Reward | None:
    if not for_update:
        return session.get(Reward, reward_id)
    return session.scalar(select(Reward).where(Reward.id == reward_id).with_for_update())


def list_rewards(session: Session, include_archived: bool = False) -> list[Reward]:
    statement = select(Reward).order_by(Reward.id)
    if not include_archived:
        statement = statement.where(Reward.status != RewardStatus.ARCHIVED)
    return list(session.scalars(statement))


def list_purchases(session: Session) -> list[RewardPurchase]:
    return list(
        session.scalars(
            select(RewardPurchase).order_by(
                RewardPurchase.purchased_at.desc(),
                RewardPurchase.id.desc(),
            )
        )
    )


MISSION_COSTS = {
    "easy": 25,
    "medium": 45,
    "hard": 70,
    "epic": 100,
}


def build_badge_suggestion_statement():
    return (
        select(Badge, EarnedBadge)
        .outerjoin(EarnedBadge, EarnedBadge.badge_id == Badge.id)
        .order_by(
            case((EarnedBadge.id.is_(None), 1), else_=0),
            EarnedBadge.earned_at.desc(),
            case((Badge.code == "first_reward", 0), else_=1),
            Badge.id,
        )
        .limit(3)
    )


def list_reward_suggestions(session: Session) -> list[RewardSuggestionRead]:
    suggestions: list[RewardSuggestionRead] = []
    recent_missions = list(
        session.scalars(
            select(Mission)
            .where(Mission.deleted_at.is_(None))
            .where(Mission.status != MissionStatus.ARCHIVED)
            .order_by(Mission.updated_at.desc(), Mission.id.desc())
            .limit(3)
        )
    )
    for mission in recent_missions:
        suggestions.append(
            RewardSuggestionRead(
                key=f"mission_{mission.id}",
                name=f"Prêmio da missão: {mission.title[:52]}",
                description=f"Compra sugerida para celebrar ou destravar a missão \"{mission.title}\".",
                cost=MISSION_COSTS.get(str(mission.difficulty), 45),
                source="mission",
                source_label="Missão",
            )
        )

    earned_count = session.scalar(select(func.count()).select_from(EarnedBadge)) or 0
    badge_rows = list(
        session.execute(build_badge_suggestion_statement())
    )
    for badge, earned_badge in badge_rows:
        is_earned = earned_badge is not None
        badge_cost = 60 if is_earned else min(120, 40 + max(1, badge.threshold) * 5)
        name_prefix = "Celebração da medalha" if is_earned else "Meta de medalha"
        description_prefix = "Você conquistou" if is_earned else "Reserve para quando desbloquear"
        suggestions.append(
            RewardSuggestionRead(
                key=f"badge_{badge.id}_{'earned' if is_earned else 'locked'}_{earned_count}",
                name=f"{name_prefix}: {badge.name}",
                description=f"{description_prefix} a medalha \"{badge.name}\".",
                cost=badge_cost,
                source="badge",
                source_label="Medalha",
            )
        )
    return suggestions


def create_reward(session: Session, data: RewardCreate) -> Reward:
    reward = Reward(**data.model_dump())
    session.add(reward)
    session.commit()
    session.refresh(reward)
    return reward


def update_reward(session: Session, reward_id: int, data: RewardUpdate) -> Reward | None:
    reward = _get_reward(session, reward_id)
    if reward is None:
        return None

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(reward, field, value)
    session.commit()
    session.refresh(reward)
    return reward


def archive_reward(session: Session, reward_id: int) -> Reward | None:
    reward = _get_reward(session, reward_id)
    if reward is None:
        return None

    reward.status = RewardStatus.ARCHIVED
    session.commit()
    session.refresh(reward)
    return reward


def purchase_reward(session: Session, reward_id: int) -> RewardPurchase | None:
    reward = _get_reward(session, reward_id, for_update=True)
    if reward is None:
        return None
    if reward.status == RewardStatus.ARCHIVED:
        raise ValueError("Reward is archived")

    player = get_player(session, for_update=True)
    if player.gold < reward.cost:
        raise ValueError("Not enough gold")

    player.gold -= reward.cost
    purchase = RewardPurchase(reward_id=reward.id, cost_paid=reward.cost)
    session.add(purchase)
    evaluate_badges(session)
    session.commit()
    session.refresh(purchase)
    return purchase
