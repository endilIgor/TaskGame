from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.schemas import BadgeStatusRead
from backend.app.services.badges import evaluate_badges, list_badges_with_status


router = APIRouter(prefix="/api/badges", tags=["badges"])


@router.get("", response_model=list[BadgeStatusRead])
def list_badges(session: Session = Depends(get_session)) -> list[BadgeStatusRead]:
    evaluate_badges(session)
    session.commit()
    return list_badges_with_status(session)
