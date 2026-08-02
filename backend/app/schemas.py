from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.models import Difficulty, MissionStatus, MissionType


class MissionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = None
    type: MissionType
    difficulty: Difficulty = Difficulty.EASY
    category: str | None = Field(default=None, max_length=80)
    start_date: date = Field(default_factory=date.today)
    target_date: date | None = None
    repeat_days: list[int] | None = None
    progress_current: int = Field(default=0, ge=0)
    progress_target: int | None = Field(default=None, ge=1)

    @field_validator("repeat_days")
    @classmethod
    def validate_repeat_days(cls, value: list[int] | None) -> list[int] | None:
        if value is not None and any(day < 0 or day > 6 for day in value):
            raise ValueError("repeat_days values must be between 0 and 6")
        return value

    @model_validator(mode="after")
    def validate_long_term_progress(self) -> "MissionCreate":
        if self.type == MissionType.LONG_TERM and self.progress_target is None:
            raise ValueError("progress_target is required for long_term missions")
        return self


class MissionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    type: MissionType | None = None
    difficulty: Difficulty | None = None
    category: str | None = Field(default=None, max_length=80)
    start_date: date | None = None
    target_date: date | None = None
    repeat_days: list[int] | None = None
    progress_target: int | None = Field(default=None, ge=1)

    @field_validator("repeat_days")
    @classmethod
    def validate_repeat_days(cls, value: list[int] | None) -> list[int] | None:
        if value is not None and any(day < 0 or day > 6 for day in value):
            raise ValueError("repeat_days values must be between 0 and 6")
        return value


class MissionProgressUpdate(BaseModel):
    amount: int = Field(gt=0)


class MissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    type: MissionType
    difficulty: Difficulty
    category: str | None
    status: MissionStatus
    start_date: date
    target_date: date | None
    repeat_days: list[int] | None
    progress_current: int
    progress_target: int | None
    created_at: datetime
    updated_at: datetime

    @field_validator("repeat_days", mode="before")
    @classmethod
    def parse_repeat_days(cls, value: str | list[int] | None) -> list[int] | None:
        if value is None or isinstance(value, list):
            return value
        return [int(day) for day in value.split(",") if day]


class MissionCompletionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mission_id: int
    completed_at: datetime
    xp_awarded: int
    gold_awarded: int
    streak_bonus_percent: int
    note: str | None


class BadgeStatusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str
    condition_type: str
    threshold: int
    earned: bool
    earned_at: datetime | None
