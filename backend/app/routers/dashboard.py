from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.schemas import DashboardRead, GoalRead
from backend.app.services.reports import build_dashboard, list_goals


router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard", response_model=DashboardRead)
def dashboard(session: Session = Depends(get_session)) -> DashboardRead:
    return build_dashboard(session)


@router.get("/api/goals", response_model=list[GoalRead])
def goals(session: Session = Depends(get_session)) -> list[GoalRead]:
    return list_goals(session)
