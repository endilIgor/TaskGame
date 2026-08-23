from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.models import Difficulty, HeroClass, MissionStatus, MissionType, SkillType


class MissionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str | None = None
    type: MissionType
    difficulty: Difficulty = Difficulty.EASY
    category: str | None = Field(default=None, max_length=80)
    skill: SkillType | None = None
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
        if self.type == MissionType.LONG_TERM:
            if self.progress_target is None:
                raise ValueError("progress_target is required for long_term missions")
            if self.target_date is None or self.target_date < self.start_date:
                raise ValueError("target_date must be on or after start_date for long_term missions")
        return self


class MissionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    type: MissionType | None = None
    difficulty: Difficulty | None = None
    category: str | None = Field(default=None, max_length=80)
    skill: SkillType | None = None
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


class MissionComplete(BaseModel):
    completed_on: date | None = None


class MissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    type: MissionType
    difficulty: Difficulty
    category: str | None
    skill: str | None
    status: MissionStatus
    start_date: date
    target_date: date | None
    repeat_days: list[int] | None
    progress_current: int
    progress_target: int | None
    completion_count: int = 0
    total_xp_awarded: int = 0
    total_gold_awarded: int = 0
    completed_today: bool = False
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
    mission_completion_count: int = 0
    mission_total_xp_awarded: int = 0
    mission_total_gold_awarded: int = 0
    unlocked_badges: list[BadgeStatusRead] = Field(default_factory=list)


class JournalEntryCreate(BaseModel):
    title: str | None = Field(default=None, max_length=140)
    entry_date: date = Field(default_factory=date.today)
    content: str = Field(min_length=1)
    mood: str | None = Field(default=None, max_length=80)


class JournalEntryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=140)
    entry_date: date | None = None
    content: str | None = Field(default=None, min_length=1)
    mood: str | None = Field(default=None, max_length=80)


class JournalEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    entry_date: date
    content: str
    mood: str | None
    created_at: datetime
    updated_at: datetime


class JournalEntrySummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    entry_date: date
    excerpt: str
    mood: str | None
    created_at: datetime
    updated_at: datetime


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


class RewardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    cost: int = Field(ge=1)


class RewardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    cost: int | None = Field(default=None, ge=1)


class RewardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    cost: int
    status: str


class RewardPurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reward_id: int
    cost_paid: int
    purchased_at: datetime


class BackupStatusRead(BaseModel):
    last_mysql_dump_at: datetime | None
    last_mysql_dump_filename: str | None


class PlayerSummaryRead(BaseModel):
    total_xp: int
    gold: int
    level: int
    xp_into_level: int
    xp_for_next_level: int
    current_streak: int
    best_streak: int


class DashboardTodayRead(BaseModel):
    completed: int
    active: int
    overdue: int


class DashboardWeeklyRead(BaseModel):
    missions_completed: int
    xp_gained: int
    gold_gained: int
    best_day: str | None


class DashboardRead(BaseModel):
    player: PlayerSummaryRead
    today: DashboardTodayRead
    weekly: DashboardWeeklyRead
    upcoming_missions: list[MissionRead]
    recent_badge: BadgeStatusRead | None


class GoalRead(MissionRead):
    progress_percent: int = Field(default=0, ge=0, le=100)


class CategoryCompletionRead(BaseModel):
    category: str
    completions: int


class ReportDayRead(BaseModel):
    date: date
    label: str
    completions: int
    xp_gained: int
    gold_gained: int


class WeeklyReportRead(BaseModel):
    period_type: str = "weekly"
    period_start: date
    period_end: date
    week_start: date
    week_end: date
    missions_completed: int
    missions_failed: int
    xp_gained: int
    gold_gained: int
    best_day: str | None
    current_streak: int
    best_streak: int
    daily_completions: list[int]
    daily_activity: list[ReportDayRead]
    top_categories: list[CategoryCompletionRead]
    goals_completed: list[str]


class OnboardingAnswers(BaseModel):
    hero_name: str = Field(min_length=1, max_length=80)
    hero_class: HeroClass
    focus_skills: list[SkillType] = Field(min_length=1, max_length=3)
    daily_minutes: int = Field(ge=5, le=240)
    preferred_days: list[int] = Field(default_factory=list)
    main_goal: str | None = Field(default=None, max_length=500)
    progress_prompt: str | None = Field(default=None, max_length=200)
    reward_style: str | None = Field(default=None, max_length=40)
    intensity: str = "balanced"

    @field_validator("preferred_days")
    @classmethod
    def validate_preferred_days(cls, value: list[int]) -> list[int]:
        if any(day < 0 or day > 6 for day in value):
            raise ValueError("preferred_days values must be between 0 and 6")
        return value

    @field_validator("intensity")
    @classmethod
    def validate_intensity(cls, value: str) -> str:
        if value not in {"light", "balanced", "hardcore"}:
            raise ValueError("intensity must be one of light, balanced, hardcore")
        return value


class PlayerProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hero_name: str
    hero_class: HeroClass
    avatar_asset: str | None
    focus_skills: list[str]
    daily_minutes: int
    preferred_days: list[int]
    main_goal: str | None
    progress_prompt: str | None
    reward_style: str | None
    intensity: str
    onboarding_completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @field_validator("focus_skills", mode="before")
    @classmethod
    def parse_focus_skills(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        return [skill for skill in value.split(",") if skill]

    @field_validator("preferred_days", mode="before")
    @classmethod
    def parse_preferred_days(cls, value: str | list[int]) -> list[int]:
        if isinstance(value, list):
            return value
        return [int(day) for day in value.split(",") if day]


class MissionSuggestionRead(BaseModel):
    key: str
    title: str
    description: str | None
    type: MissionType
    difficulty: Difficulty
    skill: SkillType
    target_date: date | None
    progress_target: int | None
    repeat_days: list[int] | None


class RewardSuggestionRead(BaseModel):
    key: str
    name: str
    description: str | None
    cost: int


class OnboardingPreviewRead(BaseModel):
    hero_name: str
    hero_class: HeroClass
    missions: list[MissionSuggestionRead]
    rewards: list[RewardSuggestionRead]
    class_badge: BadgeStatusRead


class OnboardingConfirmRequest(BaseModel):
    answers: OnboardingAnswers
    selected_mission_keys: list[str] = Field(default_factory=list)
    selected_reward_keys: list[str] = Field(default_factory=list)


class OnboardingConfirmRead(BaseModel):
    profile: PlayerProfileRead
    missions: list[MissionRead]
    rewards: list[RewardRead]
    badges: list[BadgeStatusRead]
