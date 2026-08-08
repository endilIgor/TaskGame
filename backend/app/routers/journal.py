from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_session
from backend.app.schemas import JournalEntryCreate, JournalEntryRead, JournalEntrySummaryRead, JournalEntryUpdate
from backend.app.services import journal as journal_service


router = APIRouter(prefix="/api/journal", tags=["journal"])


def _entry_or_404(entry):
    if entry is None:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.get("/entries", response_model=list[JournalEntrySummaryRead])
def list_entries(month: str | None = None, session: Session = Depends(get_session)):
    try:
        return journal_service.list_entries(session, month)
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail="month must use YYYY-MM format") from error


@router.post("/entries", response_model=JournalEntryRead, status_code=status.HTTP_201_CREATED)
def create_entry(data: JournalEntryCreate, session: Session = Depends(get_session)):
    return journal_service.create_entry(session, data)


@router.get("/entries/{entry_id}", response_model=JournalEntryRead)
def get_entry(entry_id: int, session: Session = Depends(get_session)):
    return _entry_or_404(journal_service.get_entry(session, entry_id))


@router.patch("/entries/{entry_id}", response_model=JournalEntryRead)
def update_entry(entry_id: int, data: JournalEntryUpdate, session: Session = Depends(get_session)):
    return _entry_or_404(journal_service.update_entry(session, entry_id, data))
