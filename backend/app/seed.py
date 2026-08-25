from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import Badge, HeroClass, PlayerStats


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
        "code": "daily_contracts_10",
        "name": "Ritual diário",
        "description": "Conclua 10 missões diárias para firmar sua rotina no salão.",
        "condition_type": "daily_missions_completed",
        "threshold": 10,
    },
    {
        "code": "weekly_contracts_4",
        "name": "Estrategista semanal",
        "description": "Conclua 4 missões semanais e prove consistência nos contratos maiores.",
        "condition_type": "weekly_missions_completed",
        "threshold": 4,
    },
    {
        "code": "epic_campaigns_3",
        "name": "Lenda de campanha",
        "description": "Conclua 3 missões épicas de campanha para marcar seu nome na guilda.",
        "condition_type": "epic_missions_completed",
        "threshold": 3,
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


CLASS_BADGES: dict[HeroClass, dict] = {
    HeroClass.WARRIOR: {
        "code": "class_warrior",
        "name": "Veterano da Arena",
        "description": "Medalha do personagem Guerreiro: disciplina, treino e execução desbloqueados no onboarding.",
        "condition_type": "hero_class_warrior",
        "threshold": 1,
    },
    HeroClass.MAGE: {
        "code": "class_mage",
        "name": "Mestre do Grimório",
        "description": "Medalha do personagem Mago: estudo, foco profundo e criação desbloqueados no onboarding.",
        "condition_type": "hero_class_mage",
        "threshold": 1,
    },
    HeroClass.ARCHER: {
        "code": "class_archer",
        "name": "Olho Preciso",
        "description": "Medalha do personagem Arqueiro: precisão e constância desbloqueadas no onboarding.",
        "condition_type": "hero_class_archer",
        "threshold": 1,
    },
    HeroClass.GUARDIAN: {
        "code": "class_guardian",
        "name": "Escudo da Rotina",
        "description": "Medalha do personagem Guardião: equilíbrio, cuidado e vínculos desbloqueados no onboarding.",
        "condition_type": "hero_class_guardian",
        "threshold": 1,
    },
}


def seed_defaults(session: Session) -> None:
    if session.scalar(select(PlayerStats).limit(1)) is None:
        session.add(PlayerStats())

    existing_badges = {
        badge.code: badge
        for badge in session.scalars(select(Badge)).all()
    }
    all_badges = list(DEFAULT_BADGES) + list(CLASS_BADGES.values())
    for badge_data in all_badges:
        badge = existing_badges.get(badge_data["code"])
        if badge is None:
            session.add(Badge(**badge_data))
            continue
        badge.name = badge_data["name"]
        badge.description = badge_data["description"]
        badge.condition_type = badge_data["condition_type"]
        badge.threshold = badge_data["threshold"]
    session.commit()
