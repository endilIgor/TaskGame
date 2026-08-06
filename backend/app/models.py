from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MissionType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    LONG_TERM = "long_term"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EPIC = "epic"


class SkillType(StrEnum):
    KNOWLEDGE = "knowledge"
    STRENGTH = "strength"
    MONEY = "money"
    HEALTH = "health"
    CREATIVITY = "creativity"
    SOCIAL = "social"


class MissionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class RewardStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


def enum_values(enum_class: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_class]


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[MissionType] = mapped_column(
        Enum(MissionType, values_callable=enum_values),
    )
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, values_callable=enum_values),
    )
    category: Mapped[str | None] = mapped_column(String(80))
    status: Mapped[MissionStatus] = mapped_column(
        Enum(MissionStatus, values_callable=enum_values),
        default=MissionStatus.ACTIVE,
    )
    start_date: Mapped[date] = mapped_column(Date, default=date.today)
    target_date: Mapped[date | None] = mapped_column(Date)
    repeat_days: Mapped[str | None] = mapped_column(Text)
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_target: Mapped[int | None] = mapped_column(Integer)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    completions: Mapped[list["MissionCompletion"]] = relationship(back_populates="mission")

    @property
    def skill(self) -> str | None:
        return self.category


class MissionCompletion(Base):
    __tablename__ = "mission_completions"
    __table_args__ = (
        UniqueConstraint("mission_id", "completion_key", name="uq_mission_completion_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"))
    completion_key: Mapped[str] = mapped_column(String(64))
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    xp_awarded: Mapped[int] = mapped_column(Integer)
    gold_awarded: Mapped[int] = mapped_column(Integer)
    streak_bonus_percent: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str | None] = mapped_column(Text)

    mission: Mapped[Mission] = relationship(back_populates="completions")


class PlayerStats(Base):
    __tablename__ = "player_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    gold: Mapped[int] = mapped_column(Integer, default=0)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Badge(Base):
    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    condition_type: Mapped[str] = mapped_column(String(64))
    threshold: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    earned_badges: Mapped[list["EarnedBadge"]] = relationship(back_populates="badge")


class EarnedBadge(Base):
    __tablename__ = "earned_badges"

    id: Mapped[int] = mapped_column(primary_key=True)
    badge_id: Mapped[int] = mapped_column(ForeignKey("badges.id"), unique=True)
    earned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    badge: Mapped[Badge] = relationship(back_populates="earned_badges")


class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    cost: Mapped[int] = mapped_column(Integer)
    status: Mapped[RewardStatus] = mapped_column(
        Enum(RewardStatus, values_callable=enum_values),
        default=RewardStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    purchases: Mapped[list["RewardPurchase"]] = relationship(back_populates="reward")


class RewardPurchase(Base):
    __tablename__ = "reward_purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    reward_id: Mapped[int] = mapped_column(ForeignKey("rewards.id"))
    purchased_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    cost_paid: Mapped[int] = mapped_column(Integer)

    reward: Mapped[Reward] = relationship(back_populates="purchases")


class WeeklySnapshot(Base):
    __tablename__ = "weekly_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_start: Mapped[date] = mapped_column(Date)
    week_end: Mapped[date] = mapped_column(Date)
    missions_completed: Mapped[int] = mapped_column(Integer, default=0)
    missions_failed: Mapped[int] = mapped_column(Integer, default=0)
    xp_gained: Mapped[int] = mapped_column(Integer, default=0)
    gold_gained: Mapped[int] = mapped_column(Integer, default=0)
    best_day: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
