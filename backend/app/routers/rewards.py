from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.schemas import RewardCreate, RewardPurchaseRead, RewardRead, RewardUpdate
from backend.app.services import rewards as reward_service


router = APIRouter(prefix="/api/rewards", tags=["rewards"])


def _reward_or_404(reward):
    if reward is None:
        raise HTTPException(status_code=404, detail="Reward not found")
    return reward


@router.get("", response_model=list[RewardRead])
def list_rewards(
    include_archived: bool = False,
    session: Session = Depends(get_session),
):
    return reward_service.list_rewards(session, include_archived)


@router.post("", response_model=RewardRead, status_code=status.HTTP_201_CREATED)
def create_reward(data: RewardCreate, session: Session = Depends(get_session)):
    return reward_service.create_reward(session, data)


@router.patch("/{reward_id}", response_model=RewardRead)
def update_reward(
    reward_id: int,
    data: RewardUpdate,
    session: Session = Depends(get_session),
):
    return _reward_or_404(reward_service.update_reward(session, reward_id, data))


@router.post("/{reward_id}/purchase", response_model=RewardPurchaseRead)
def purchase_reward(reward_id: int, session: Session = Depends(get_session)):
    try:
        purchase = reward_service.purchase_reward(session, reward_id)
    except ValueError as error:
        if str(error) == "Not enough gold":
            raise HTTPException(status_code=400, detail="Not enough gold") from error
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _reward_or_404(purchase)


@router.post("/{reward_id}/archive", response_model=RewardRead)
def archive_reward(reward_id: int, session: Session = Depends(get_session)):
    return _reward_or_404(reward_service.archive_reward(session, reward_id))
