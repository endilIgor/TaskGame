from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Badge, PlayerStats


DEFAULT_BADGES = (
    {
        "code": "streak_7",
        "name": "Sequência de 7 dias",
        "description": "Conclua missões diárias por 7 dias seguidos.",
        "condition_type": "streak",
        "threshold": 7,
    },
    {
        "code": "streak_30",
        "name": "Sequência de 30 dias",
        "description": "Conclua missões diárias por 30 dias seguidos.",
        "condition_type": "streak",
        "threshold": 30,
    },
    {
        "code": "missions_100",
        "name": "100 missões concluídas",
        "description": "Conclua 100 missões.",
        "condition_type": "missions_completed",
        "threshold": 100,
    },
    {
        "code": "first_goal",
        "name": "Primeiro objetivo concluído",
        "description": "Conclua seu primeiro objetivo longo.",
        "condition_type": "goals_completed",
        "threshold": 1,
    },
    {
        "code": "perfect_week",
        "name": "Rotina perfeita da semana",
        "description": "Conclua ao menos 7 missões em uma semana sem falhas.",
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

    existing_badges = {
        badge.code: badge
        for badge in session.scalars(select(Badge)).all()
    }
    for badge_data in DEFAULT_BADGES:
        badge = existing_badges.get(badge_data["code"])
        if badge is None:
            session.add(Badge(**badge_data))
            continue
        badge.name = badge_data["name"]
        badge.description = badge_data["description"]
        badge.condition_type = badge_data["condition_type"]
        badge.threshold = badge_data["threshold"]
    session.commit()
