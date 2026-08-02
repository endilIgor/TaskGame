from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Badge, PlayerStats


DEFAULT_BADGES = (
    {
        "code": "streak_7",
        "name": "Sequencia de 7 dias",
        "description": "Conclua missoes diarias por 7 dias seguidos.",
        "condition_type": "streak",
        "threshold": 7,
    },
    {
        "code": "streak_30",
        "name": "Sequencia de 30 dias",
        "description": "Conclua missoes diarias por 30 dias seguidos.",
        "condition_type": "streak",
        "threshold": 30,
    },
    {
        "code": "missions_100",
        "name": "100 missoes concluidas",
        "description": "Conclua 100 missoes.",
        "condition_type": "missions_completed",
        "threshold": 100,
    },
    {
        "code": "first_goal",
        "name": "Primeiro objetivo concluido",
        "description": "Conclua seu primeiro objetivo longo.",
        "condition_type": "goals_completed",
        "threshold": 1,
    },
    {
        "code": "perfect_week",
        "name": "Rotina perfeita da semana",
        "description": "Conclua ao menos 7 missoes em uma semana sem falhas.",
        "condition_type": "perfect_week",
        "threshold": 7,
    },
    {
        "code": "first_reward",
        "name": "Primeira compra na loja",
        "description": "Compre sua primeira recompensa.",
        "condition_type": "rewards_purchased",
        "threshold": 1,
    },
    {
        "code": "xp_1000",
        "name": "1000 XP acumulados",
        "description": "Acumule 1000 XP.",
        "condition_type": "total_xp",
        "threshold": 1000,
    },
    {
        "code": "xp_10000",
        "name": "10000 XP acumulados",
        "description": "Acumule 10000 XP.",
        "condition_type": "total_xp",
        "threshold": 10000,
    },
)


def seed_defaults(session: Session) -> None:
    if session.scalar(select(PlayerStats).limit(1)) is None:
        session.add(PlayerStats())

    existing_codes = set(session.scalars(select(Badge.code)).all())
    session.add_all(
        Badge(**badge)
        for badge in DEFAULT_BADGES
        if badge["code"] not in existing_codes
    )
    session.commit()
