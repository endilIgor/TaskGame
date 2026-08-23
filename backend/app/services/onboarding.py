from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models import (
    Badge,
    Difficulty,
    EarnedBadge,
    HeroClass,
    Mission,
    MissionStatus,
    MissionType,
    PlayerProfile,
    Reward,
    RewardStatus,
    SkillType,
)
from backend.app.schemas import (
    BadgeStatusRead,
    MissionSuggestionRead,
    OnboardingAnswers,
    OnboardingConfirmRead,
    OnboardingPreviewRead,
    PlayerProfileRead,
    RewardSuggestionRead,
)
from backend.app.services.badges import evaluate_badges

CAMPAIGN_LENGTH_DAYS = 30

INTENSITY_DIFFICULTY: dict[str, Difficulty] = {
    "light": Difficulty.EASY,
    "balanced": Difficulty.MEDIUM,
    "hardcore": Difficulty.HARD,
}

CLASS_FLAVOR_WORDS: dict[HeroClass, list[str]] = {
    HeroClass.WARRIOR: ["Treino", "Forja", "Arena"],
    HeroClass.MAGE: ["Grimório", "Ritual", "Estudo"],
    HeroClass.ARCHER: ["Alvo", "Precisão", "Patrulha"],
    HeroClass.GUARDIAN: ["Proteção", "Fortaleza", "Cuidado"],
}

SKILL_DAILY_TEMPLATES: dict[SkillType, list[tuple[str, str]]] = {
    SkillType.KNOWLEDGE: [
        ("Estudar 15 minutos", "Dedique um tempo curto a aprender algo novo."),
        ("Ler um pouco", "Leia um trecho de um livro ou artigo."),
        ("Revisar anotações", "Revise algo que você aprendeu recentemente."),
    ],
    SkillType.STRENGTH: [
        ("Fazer treino curto", "Um treino rápido para manter o ritmo."),
        ("Alongar o corpo", "Movimente o corpo por alguns minutos."),
        ("Treino de força", "Faça exercícios de força hoje."),
    ],
    SkillType.MONEY: [
        ("Revisar gastos do dia", "Confira rapidamente para onde foi o dinheiro hoje."),
        ("Planejar um gasto", "Pense antes de gastar algo hoje."),
        ("Guardar um pouco", "Separe uma pequena quantia para sua meta."),
    ],
    SkillType.HEALTH: [
        ("Beber água e caminhar", "Cuide do corpo com água e um pouco de movimento."),
        ("Dormir cedo", "Priorize o descanso essa noite."),
        ("Cuidar da alimentação", "Faça uma escolha saudável em uma refeição."),
    ],
    SkillType.CREATIVITY: [
        ("Criar algo por 15 minutos", "Escreva, desenhe ou produza algo pequeno."),
        ("Explorar uma ideia nova", "Anote uma ideia criativa que surgir hoje."),
        ("Praticar uma habilidade criativa", "Dedique um tempo curto a criar."),
    ],
    SkillType.SOCIAL: [
        ("Mandar mensagem para alguém importante", "Fortaleça um vínculo com uma mensagem."),
        ("Agradecer alguém", "Demonstre gratidão a uma pessoa importante."),
        ("Puxar uma conversa", "Converse com alguém que você gosta."),
    ],
}

SKILL_WEEKLY_TEMPLATES: dict[SkillType, tuple[str, str]] = {
    SkillType.KNOWLEDGE: ("Registrar 3 aprendizados da semana", "Anote 3 coisas que você aprendeu essa semana."),
    SkillType.STRENGTH: ("Completar 3 treinos na semana", "Feche a semana com 3 treinos concluídos."),
    SkillType.MONEY: ("Planejar uma melhoria financeira", "Defina uma ação financeira para essa semana."),
    SkillType.HEALTH: ("Preparar rotina saudável da semana", "Organize sua semana com foco em saúde."),
    SkillType.CREATIVITY: ("Publicar/organizar uma criação", "Finalize ou compartilhe algo que você criou."),
    SkillType.SOCIAL: ("Fortalecer um vínculo", "Dedique um tempo a alguém importante essa semana."),
}

REWARD_STYLE_TEMPLATES: dict[str, tuple[str, str]] = {
    "rest": ("Pausa para descansar", "Um tempo de descanso ou lazer sem culpa."),
    "food": ("Mimo gostoso", "Uma comida ou presente especial."),
    "game": ("Sessão de jogo ou filme", "Tempo livre para jogar ou assistir algo."),
    "planned_purchase": ("Compra planejada", "Um item que você está economizando para comprar."),
}


def _class_badge_code(hero_class: HeroClass) -> str:
    return f"class_{hero_class.value}"


def _skills_for_daily_slots(focus_skills: list[SkillType]) -> list[tuple[SkillType, int]]:
    if len(focus_skills) >= 3:
        return [(skill, 0) for skill in focus_skills[:3]]
    if len(focus_skills) == 2:
        return [(focus_skills[0], 0), (focus_skills[1], 0), (focus_skills[0], 1)]
    return [(focus_skills[0], 0), (focus_skills[0], 1), (focus_skills[0], 2)]


def _daily_missions(answers: OnboardingAnswers) -> list[MissionSuggestionRead]:
    flavors = CLASS_FLAVOR_WORDS[answers.hero_class]
    difficulty = INTENSITY_DIFFICULTY[answers.intensity]
    slots = _skills_for_daily_slots(answers.focus_skills)
    missions = []
    for index, (skill, variant_index) in enumerate(slots):
        variants = SKILL_DAILY_TEMPLATES[skill]
        title, description = variants[variant_index % len(variants)]
        flavor = flavors[index % len(flavors)]
        missions.append(
            MissionSuggestionRead(
                key=f"daily_{index + 1}",
                title=f"{flavor}: {title}",
                description=f"{description} (~{answers.daily_minutes} min)",
                type=MissionType.DAILY,
                difficulty=difficulty,
                skill=skill,
                target_date=None,
                progress_target=None,
                repeat_days=answers.preferred_days or None,
            )
        )
    return missions


def _weekly_mission(answers: OnboardingAnswers) -> MissionSuggestionRead:
    difficulty = INTENSITY_DIFFICULTY[answers.intensity]
    flavor = CLASS_FLAVOR_WORDS[answers.hero_class][0]
    primary_skill = answers.focus_skills[0]
    title, description = SKILL_WEEKLY_TEMPLATES[primary_skill]
    return MissionSuggestionRead(
        key="weekly_1",
        title=f"{flavor} Semanal: {title}",
        description=description,
        type=MissionType.WEEKLY,
        difficulty=difficulty,
        skill=primary_skill,
        target_date=None,
        progress_target=None,
        repeat_days=None,
    )


def _campaign_mission(answers: OnboardingAnswers, today: date) -> MissionSuggestionRead:
    primary_skill = answers.focus_skills[0]
    title = answers.main_goal.strip() if answers.main_goal and answers.main_goal.strip() else f"Campanha de 30 dias: {SKILL_WEEKLY_TEMPLATES[primary_skill][0]}"
    description = answers.progress_prompt.strip() if answers.progress_prompt and answers.progress_prompt.strip() else "Avance um pouco todos os dias rumo à sua meta de 30 dias."
    return MissionSuggestionRead(
        key="campaign_1",
        title=title,
        description=description,
        type=MissionType.LONG_TERM,
        difficulty=Difficulty.EPIC,
        skill=primary_skill,
        target_date=today + timedelta(days=CAMPAIGN_LENGTH_DAYS),
        progress_target=CAMPAIGN_LENGTH_DAYS,
        repeat_days=None,
    )


def _reward_suggestions(answers: OnboardingAnswers) -> list[RewardSuggestionRead]:
    name, description = REWARD_STYLE_TEMPLATES.get(answers.reward_style or "rest", REWARD_STYLE_TEMPLATES["rest"])
    return [
        RewardSuggestionRead(key="reward_small", name=f"{name} (rápido)", description=description, cost=30),
        RewardSuggestionRead(key="reward_big", name=f"{name} (especial)", description=description, cost=90),
    ]


def _class_badge_suggestion(hero_class: HeroClass) -> BadgeStatusRead:
    from backend.app.seed import CLASS_BADGES

    badge_data = CLASS_BADGES[hero_class]
    return BadgeStatusRead(
        id=0,
        code=badge_data["code"],
        name=badge_data["name"],
        description=badge_data["description"],
        condition_type=badge_data["condition_type"],
        threshold=badge_data["threshold"],
        earned=False,
        earned_at=None,
    )


def build_onboarding_preview(answers: OnboardingAnswers, today: date | None = None) -> OnboardingPreviewRead:
    effective_today = today or date.today()
    missions = _daily_missions(answers) + [_weekly_mission(answers), _campaign_mission(answers, effective_today)]
    return OnboardingPreviewRead(
        hero_name=answers.hero_name,
        hero_class=answers.hero_class,
        missions=missions,
        rewards=_reward_suggestions(answers),
        class_badge=_class_badge_suggestion(answers.hero_class),
    )


def get_player_profile(session: Session) -> PlayerProfile | None:
    return session.scalar(select(PlayerProfile).limit(1))


def _create_mission_from_suggestion(suggestion: MissionSuggestionRead) -> Mission:
    return Mission(
        title=suggestion.title,
        description=suggestion.description,
        type=suggestion.type,
        difficulty=suggestion.difficulty,
        category=suggestion.skill.value,
        status=MissionStatus.ACTIVE,
        start_date=date.today(),
        target_date=suggestion.target_date,
        repeat_days=(",".join(str(day) for day in suggestion.repeat_days) if suggestion.repeat_days else None),
        progress_current=0,
        progress_target=suggestion.progress_target,
    )


def confirm_onboarding(
    session: Session,
    answers: OnboardingAnswers,
    selected_mission_keys: list[str],
    selected_reward_keys: list[str],
) -> OnboardingConfirmRead:
    existing_profile = get_player_profile(session)
    if existing_profile is not None and existing_profile.onboarding_completed_at is not None:
        badge_code = _class_badge_code(existing_profile.hero_class)
        badge_row = session.execute(
            select(Badge, EarnedBadge)
            .join(EarnedBadge, EarnedBadge.badge_id == Badge.id)
            .where(Badge.code == badge_code)
        ).first()
        badges = []
        if badge_row is not None:
            badge, earned_badge = badge_row
            badges.append(
                BadgeStatusRead(
                    id=badge.id,
                    code=badge.code,
                    name=badge.name,
                    description=badge.description,
                    condition_type=badge.condition_type,
                    threshold=badge.threshold,
                    earned=True,
                    earned_at=earned_badge.earned_at,
                )
            )
        return OnboardingConfirmRead(
            profile=PlayerProfileRead.model_validate(existing_profile),
            missions=[],
            rewards=[],
            badges=badges,
        )

    preview = build_onboarding_preview(answers)
    missions_by_key = {mission.key: mission for mission in preview.missions}
    rewards_by_key = {reward.key: reward for reward in preview.rewards}

    profile = existing_profile or PlayerProfile()
    profile.hero_name = answers.hero_name
    profile.hero_class = answers.hero_class
    profile.avatar_asset = f"/assets/heroes/{answers.hero_class.value}.svg"
    profile.focus_skills = ",".join(skill.value for skill in answers.focus_skills)
    profile.daily_minutes = answers.daily_minutes
    profile.preferred_days = ",".join(str(day) for day in answers.preferred_days)
    profile.main_goal = answers.main_goal
    profile.progress_prompt = answers.progress_prompt
    profile.reward_style = answers.reward_style
    profile.intensity = answers.intensity
    profile.onboarding_completed_at = datetime.now()
    if existing_profile is None:
        session.add(profile)
    session.flush()

    created_missions = [
        _create_mission_from_suggestion(missions_by_key[key])
        for key in selected_mission_keys
        if key in missions_by_key
    ]
    session.add_all(created_missions)

    created_rewards = [
        Reward(
            name=rewards_by_key[key].name,
            description=rewards_by_key[key].description,
            cost=rewards_by_key[key].cost,
            status=RewardStatus.ACTIVE,
        )
        for key in selected_reward_keys
        if key in rewards_by_key
    ]
    session.add_all(created_rewards)
    session.flush()

    newly_earned = evaluate_badges(session)
    session.flush()
    unlocked_badges = [
        BadgeStatusRead(
            id=earned_badge.badge.id,
            code=earned_badge.badge.code,
            name=earned_badge.badge.name,
            description=earned_badge.badge.description,
            condition_type=earned_badge.badge.condition_type,
            threshold=earned_badge.badge.threshold,
            earned=True,
            earned_at=earned_badge.earned_at,
        )
        for earned_badge in newly_earned
        if earned_badge.badge.code == _class_badge_code(answers.hero_class)
    ]

    session.commit()
    session.refresh(profile)
    for mission in created_missions:
        session.refresh(mission)
    for reward in created_rewards:
        session.refresh(reward)

    return OnboardingConfirmRead(
        profile=PlayerProfileRead.model_validate(profile),
        missions=created_missions,
        rewards=created_rewards,
        badges=unlocked_badges,
    )
