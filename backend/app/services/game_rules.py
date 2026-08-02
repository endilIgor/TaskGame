from backend.app.models import Difficulty


REWARD_TABLE: dict[str, tuple[int, int]] = {
    Difficulty.EASY.value: (10, 5),
    Difficulty.MEDIUM.value: (25, 12),
    Difficulty.HARD.value: (50, 25),
    Difficulty.EPIC.value: (100, 60),
}


def base_rewards(difficulty: Difficulty | str) -> tuple[int, int]:
    key = difficulty.value if isinstance(difficulty, Difficulty) else difficulty
    return REWARD_TABLE[key]


def streak_bonus_percent(current_streak: int) -> int:
    if current_streak >= 30:
        return 25
    if current_streak >= 14:
        return 15
    if current_streak >= 7:
        return 10
    if current_streak >= 3:
        return 5
    return 0


def apply_xp_bonus(base_xp: int, bonus_percent: int) -> int:
    return int(base_xp * (1 + bonus_percent / 100))


def level_from_total_xp(total_xp: int) -> tuple[int, int, int]:
    level = 1
    remaining = total_xp
    while remaining >= 100 * level:
        remaining -= 100 * level
        level += 1
    return level, remaining, 100 * level
