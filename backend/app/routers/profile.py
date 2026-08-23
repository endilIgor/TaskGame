from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.schemas import (
    OnboardingAnswers,
    OnboardingConfirmRead,
    OnboardingConfirmRequest,
    OnboardingPreviewRead,
    PlayerProfileRead,
)
from backend.app.services import onboarding as onboarding_service


router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/profile", response_model=PlayerProfileRead)
def get_profile(session: Session = Depends(get_session)):
    profile = onboarding_service.get_player_profile(session)
    if profile is None or profile.onboarding_completed_at is None:
        raise HTTPException(status_code=404, detail="Player profile not found")
    return profile


@router.post("/onboarding/preview", response_model=OnboardingPreviewRead)
def preview_onboarding(answers: OnboardingAnswers):
    return onboarding_service.build_onboarding_preview(answers)


@router.post("/onboarding/confirm", response_model=OnboardingConfirmRead)
def confirm_onboarding(data: OnboardingConfirmRequest, session: Session = Depends(get_session)):
    return onboarding_service.confirm_onboarding(
        session,
        data.answers,
        data.selected_mission_keys,
        data.selected_reward_keys,
    )
