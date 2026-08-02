from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.schemas import WeeklyReportRead
from backend.app.services.reports import build_weekly_report


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/weekly", response_model=WeeklyReportRead)
def weekly_report(session: Session = Depends(get_session)) -> WeeklyReportRead:
    return build_weekly_report(session)


@router.get("/weekly/{week_start}", response_model=WeeklyReportRead)
def weekly_report_for_week(
    week_start: date,
    session: Session = Depends(get_session),
) -> WeeklyReportRead:
    return build_weekly_report(session, week_start)
