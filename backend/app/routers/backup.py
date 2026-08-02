from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.services.backup import completions_csv, export_all_json, missions_csv


router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("/export.json")
def export_json(session: Session = Depends(get_session)) -> JSONResponse:
    return JSONResponse(
        content=export_all_json(session),
        headers={"Content-Disposition": 'attachment; filename="taskgame-backup.json"'},
    )


@router.get("/missions.csv")
def export_missions_csv(session: Session = Depends(get_session)) -> Response:
    return Response(
        content=missions_csv(session),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="taskgame-missions.csv"'},
    )


@router.get("/completions.csv")
def export_completions_csv(session: Session = Depends(get_session)) -> Response:
    return Response(
        content=completions_csv(session),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="taskgame-completions.csv"'},
    )
