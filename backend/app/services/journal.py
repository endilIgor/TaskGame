from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import JournalEntry
from backend.app.schemas import JournalEntryCreate, JournalEntrySummaryRead, JournalEntryUpdate


def _default_title(entry_date: date) -> str:
    return f"Diario de {entry_date.strftime('%d/%m/%Y')}"


def _excerpt(content: str, limit: int = 140) -> str:
    compact = " ".join(content.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 1].rstrip()}…"


def _summary(entry: JournalEntry) -> JournalEntrySummaryRead:
    return JournalEntrySummaryRead(
        id=entry.id,
        title=entry.title,
        entry_date=entry.entry_date,
        excerpt=_excerpt(entry.content),
        mood=entry.mood,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def list_entries(session: Session, month: str | None = None) -> list[JournalEntrySummaryRead]:
    statement = select(JournalEntry)
    if month:
        year_text, month_text = month.split("-", 1)
        year = int(year_text)
        month_number = int(month_text)
        start = date(year, month_number, 1)
        if month_number == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month_number + 1, 1)
        statement = statement.where(JournalEntry.entry_date >= start).where(JournalEntry.entry_date < end)
    entries = session.scalars(statement.order_by(JournalEntry.entry_date.desc(), JournalEntry.id.desc()))
    return [_summary(entry) for entry in entries]


def get_entry(session: Session, entry_id: int) -> JournalEntry | None:
    return session.get(JournalEntry, entry_id)


def create_entry(session: Session, data: JournalEntryCreate) -> JournalEntry:
    title = data.title.strip() if data.title else ""
    entry = JournalEntry(
        title=title or _default_title(data.entry_date),
        entry_date=data.entry_date,
        content=data.content.strip(),
        mood=data.mood.strip() if data.mood else None,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def update_entry(session: Session, entry_id: int, data: JournalEntryUpdate) -> JournalEntry | None:
    entry = get_entry(session, entry_id)
    if entry is None:
        return None
    values = data.model_dump(exclude_unset=True)
    for field, value in values.items():
        if isinstance(value, str):
            value = value.strip()
        if field == "title" and not value:
            value = _default_title(values.get("entry_date", entry.entry_date))
        setattr(entry, field, value)
    session.commit()
    session.refresh(entry)
    return entry
