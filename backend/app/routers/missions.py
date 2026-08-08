from datetime import date

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.schemas import (
    MissionCompletionRead,
    MissionComplete,
    MissionCreate,
    MissionProgressUpdate,
    MissionRead,
    MissionUpdate,
)
from backend.app.services import missions as mission_service


router = APIRouter(prefix="/api/missions", tags=["missions"])


def _mission_or_404(mission):
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.get("", response_model=list[MissionRead])
def list_missions(
    include_archived: bool = False,
    today: date | None = None,
    session: Session = Depends(get_session),
):
    return mission_service.list_missions(session, include_archived, today)


@router.post("", response_model=MissionRead, status_code=status.HTTP_201_CREATED)
def create_mission(data: MissionCreate, session: Session = Depends(get_session)):
    return mission_service.create_mission(session, data)


@router.patch("/{mission_id}", response_model=MissionRead)
def update_mission(
    mission_id: int,
    data: MissionUpdate,
    session: Session = Depends(get_session),
):
    try:
        mission = mission_service.update_mission(session, mission_id, data)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _mission_or_404(mission)


@router.post("/{mission_id}/archive", response_model=MissionRead)
def archive_mission(mission_id: int, session: Session = Depends(get_session)):
    return _mission_or_404(mission_service.archive_mission(session, mission_id))


@router.post("/{mission_id}/restore", response_model=MissionRead)
def restore_mission(mission_id: int, session: Session = Depends(get_session)):
    return _mission_or_404(mission_service.restore_mission(session, mission_id))


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mission(mission_id: int, session: Session = Depends(get_session)):
    deleted = mission_service.delete_mission(session, mission_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mission not found")
    return None


@router.post("/{mission_id}/progress", response_model=MissionRead)
def advance_mission_progress(
    mission_id: int,
    data: MissionProgressUpdate,
    session: Session = Depends(get_session),
):
    try:
        mission = mission_service.advance_mission_progress(session, mission_id, data)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _mission_or_404(mission)


@router.post("/{mission_id}/complete", response_model=MissionCompletionRead)
def complete_mission(
    mission_id: int,
    data: MissionComplete | None = Body(default=None),
    session: Session = Depends(get_session),
):
    try:
        completion = mission_service.complete_mission(
            session,
            mission_id,
            data.completed_on if data else None,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return _mission_or_404(completion)
