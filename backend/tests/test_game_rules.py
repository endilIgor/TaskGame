from backend.app.models import Difficulty
from backend.app.services.game_rules import (
    apply_xp_bonus,
    base_rewards,
    level_from_total_xp,
    streak_bonus_percent,
)


def test_base_rewards_follow_spec():
    assert base_rewards(Difficulty.EASY) == (10, 5)
    assert base_rewards(Difficulty.MEDIUM) == (25, 12)
    assert base_rewards(Difficulty.HARD) == (50, 25)
    assert base_rewards(Difficulty.EPIC) == (100, 60)


def test_streak_bonus_thresholds():
    assert streak_bonus_percent(0) == 0
    assert streak_bonus_percent(3) == 5
    assert streak_bonus_percent(7) == 10
    assert streak_bonus_percent(14) == 15
    assert streak_bonus_percent(30) == 25


def test_apply_xp_bonus_rounds_down_to_integer():
    assert apply_xp_bonus(25, 10) == 27
    assert apply_xp_bonus(100, 25) == 125


def test_level_from_total_xp_uses_accumulated_thresholds():
    assert level_from_total_xp(0) == (1, 0, 100)
    assert level_from_total_xp(100) == (2, 0, 200)
    assert level_from_total_xp(299) == (2, 199, 200)
    assert level_from_total_xp(300) == (3, 0, 300)
