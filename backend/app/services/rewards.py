from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Reward, RewardPurchase, RewardStatus
from backend.app.schemas import RewardCreate, RewardUpdate
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
