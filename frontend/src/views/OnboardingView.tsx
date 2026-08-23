import { useState } from "react";
import { apiPost } from "../api/client";
import { FormField, TextInput } from "../components/FormControls";
import { GameIcon } from "../components/GameIcon";
import { ErrorPanel } from "../components/StatePanels";
import { HERO_CLASSES, heroClassById } from "../data/heroClasses";
import type {
  HeroClass,
  MissionSuggestion,
  OnboardingAnswers,
  OnboardingConfirmPayload,
  OnboardingConfirmResult,
  OnboardingPreviewResult,
  RewardSuggestion,
  SkillType,
} from "../types";

interface OnboardingViewProps {
  onComplete: () => void;
}

const SKILL_OPTIONS: { value: SkillType; label: string }[] = [
  { value: "knowledge", label: "Conhecimento" },
  { value: "strength", label: "Força/treino" },
  { value: "money", label: "Dinheiro/carreira" },
  { value: "health", label: "Saúde" },
  { value: "creativity", label: "Criatividade" },
  { value: "social", label: "Social/família" },
];

const DAY_OPTIONS = [
  { value: 0, label: "Seg" },
  { value: 1, label: "Ter" },
  { value: 2, label: "Qua" },
  { value: 3, label: "Qui" },
  { value: 4, label: "Sex" },
  { value: 5, label: "Sáb" },
  { value: 6, label: "Dom" },
];

const MINUTE_OPTIONS = [5, 15, 30, 60];

const REWARD_STYLE_OPTIONS = [
  { value: "rest", label: "Descanso/lazer" },
  { value: "food", label: "Comida/presente" },
  { value: "game", label: "Jogo/filme" },
  { value: "planned_purchase", label: "Compra planejada" },
];

const INTENSITY_OPTIONS = [
  { value: "light", label: "Leve" },
  { value: "balanced", label: "Equilibrado" },
  { value: "hardcore", label: "Hardcore" },
];

const MISSION_TYPE_LABELS: Record<MissionSuggestion["type"], string> = {
  daily: "Diária",
  weekly: "Semanal",
  long_term: "Campanha de 30 dias",
};

const initialForm = {
  hero_name: "",
  hero_class: null as HeroClass | null,
  focus_skills: [] as SkillType[],
  daily_minutes: 15,
  preferred_days: [0, 1, 2, 3, 4] as number[],
  main_goal: "",
  progress_prompt: "",
  reward_style: "rest",
  intensity: "balanced",
};

type OnboardingForm = typeof initialForm;

function toggleValue<T>(list: T[], value: T): T[] {
  return list.includes(value) ? list.filter((item) => item !== value) : [...list, value];
}

function validateStep(step: number, form: OnboardingForm): string | null {
  if (step === 0) {
    if (!form.hero_name.trim()) return "Informe o nome do seu herói.";
    if (!form.hero_class) return "Escolha uma classe para o seu herói.";
  }
  if (step === 1) {
    if (form.focus_skills.length < 1) return "Escolha ao menos uma área para evoluir.";
    if (form.focus_skills.length > 3) return "Escolha no máximo 3 áreas.";
  }
  return null;
}

function answersFromForm(form: OnboardingForm): OnboardingAnswers {
  return {
    hero_name: form.hero_name.trim(),
    hero_class: form.hero_class as HeroClass,
    focus_skills: form.focus_skills,
    daily_minutes: form.daily_minutes,
    preferred_days: form.preferred_days,
    main_goal: form.main_goal.trim() || null,
    progress_prompt: form.progress_prompt.trim() || null,
    reward_style: form.reward_style,
    intensity: form.intensity,
  };
}

export function OnboardingView({ onComplete }: OnboardingViewProps) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<OnboardingForm>(initialForm);
  const [phase, setPhase] = useState<"questions" | "confirm">("questions");
  const [preview, setPreview] = useState<OnboardingPreviewResult | null>(null);
  const [selectedMissionKeys, setSelectedMissionKeys] = useState<string[]>([]);
  const [selectedRewardKeys, setSelectedRewardKeys] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const selectedHeroClass = form.hero_class ? heroClassById(form.hero_class) : null;

  async function goToPreview() {
    const validationError = validateStep(1, form);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setBusy(true);
    try {
      const answers = answersFromForm(form);
      const result = await apiPost<OnboardingPreviewResult, OnboardingAnswers>("/onboarding/preview", answers);
      setPreview(result);
      setSelectedMissionKeys(result.missions.map((mission) => mission.key));
      setSelectedRewardKeys(result.rewards.map((reward) => reward.key));
      setPhase("confirm");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível gerar sugestões.");
    } finally {
      setBusy(false);
    }
  }

  function goNext() {
    const validationError = validateStep(step, form);
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    if (step === 4) {
      void goToPreview();
      return;
    }
    setStep((current) => current + 1);
  }

  function goBack() {
    setError(null);
    if (phase === "confirm") {
      setPhase("questions");
      return;
    }
    setStep((current) => Math.max(0, current - 1));
  }

  async function confirmOnboarding() {
    setError(null);
    setBusy(true);
    try {
      const payload: OnboardingConfirmPayload = {
        answers: answersFromForm(form),
        selected_mission_keys: selectedMissionKeys,
        selected_reward_keys: selectedRewardKeys,
      };
      await apiPost<OnboardingConfirmResult, OnboardingConfirmPayload>("/onboarding/confirm", payload);
      onComplete();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível confirmar a aventura.");
    } finally {
      setBusy(false);
    }
  }

  function renderHeroPreview() {
    return (
      <aside
        className={`hero-sprite-card panel${selectedHeroClass ? ` accent-${selectedHeroClass.accent}` : ""}`}
        aria-label="Seu herói"
      >
        <span className="section-kicker">Seu herói</span>
        <div className="hero-sprite-frame">
          {selectedHeroClass ? (
            <img className="hero-sprite-image" src={selectedHeroClass.sprite} alt={selectedHeroClass.label} />
          ) : (
            <div className="hero-sprite-placeholder" aria-hidden="true" />
          )}
        </div>
        <div className="hero-sprite-copy">
          <h3>{form.hero_name.trim() || "Sem nome ainda"}</h3>
          <p>{selectedHeroClass ? selectedHeroClass.label : "Escolha uma classe"}</p>
          {selectedHeroClass ? <span className="hero-sprite-role">{selectedHeroClass.role}</span> : null}
        </div>
      </aside>
    );
  }

  function renderQuestions() {
    return (
      <>
        {step === 0 ? (
          <section className="panel onboarding-step" aria-labelledby="onboarding-step-heading">
            <span className="section-kicker">Identidade do herói</span>
            <h2 id="onboarding-step-heading" className="panel-heading">Qual será o nome do seu herói?</h2>
            <FormField label="Nome do herói">
              <TextInput
                required
                maxLength={80}
                placeholder="Ex: Aria"
                value={form.hero_name}
                onChange={(event) => setForm({ ...form, hero_name: event.target.value })}
              />
            </FormField>
            <h2 className="panel-heading">Escolha sua classe</h2>
            <p>A classe define o tom das missões e recompensas sugeridas — dá para ajustar depois.</p>
            <div className="class-grid">
              {HERO_CLASSES.map((heroClass) => (
                <button
                  key={heroClass.id}
                  type="button"
                  className={`class-card accent-${heroClass.accent}${form.hero_class === heroClass.id ? " selected" : ""}`}
                  onClick={() => setForm({ ...form, hero_class: heroClass.id })}
                  aria-pressed={form.hero_class === heroClass.id}
                >
                  <span className="class-card-check" aria-hidden="true">✓</span>
                  <img className="class-card-sprite" src={heroClass.sprite} alt="" aria-hidden="true" />
                  <span className="class-card-role">{heroClass.role}</span>
                  <span className="class-card-label">{heroClass.label}</span>
                  <span className="class-card-tagline">{heroClass.tagline}</span>
                  <span className="class-card-traits">
                    {heroClass.traits.map((trait) => (
                      <span key={trait} className="class-card-trait">{trait}</span>
                    ))}
                  </span>
                  <span className="class-card-skills">
                    {heroClass.focusSkills.map((skill) => SKILL_OPTIONS.find((option) => option.value === skill)?.label).join(" · ")}
                  </span>
                </button>
              ))}
            </div>
          </section>
        ) : null}

        {step === 1 ? (
          <section className="panel onboarding-step" aria-labelledby="onboarding-step-heading">
            <span className="section-kicker">Áreas de evolução</span>
            <h2 id="onboarding-step-heading" className="panel-heading">Quais áreas você quer evoluir agora?</h2>
            <p>Escolha entre 1 e 3 áreas.</p>
            <div className="choice-pill-row">
              {SKILL_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`choice-pill${form.focus_skills.includes(option.value) ? " selected" : ""}`}
                  aria-pressed={form.focus_skills.includes(option.value)}
                  onClick={() => setForm({ ...form, focus_skills: toggleValue(form.focus_skills, option.value) })}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </section>
        ) : null}

        {step === 2 ? (
          <section className="panel onboarding-step" aria-labelledby="onboarding-step-heading">
            <span className="section-kicker">Rotina</span>
            <h2 id="onboarding-step-heading" className="panel-heading">Quantos minutos por dia você consegue dedicar?</h2>
            <div className="choice-pill-row">
              {MINUTE_OPTIONS.map((minutes) => (
                <button
                  key={minutes}
                  type="button"
                  className={`choice-pill${form.daily_minutes === minutes ? " selected" : ""}`}
                  aria-pressed={form.daily_minutes === minutes}
                  onClick={() => setForm({ ...form, daily_minutes: minutes })}
                >
                  {minutes} min
                </button>
              ))}
            </div>
            <h2 className="panel-heading">Em quais dias você quer missões diárias?</h2>
            <div className="choice-pill-row">
              <button
                type="button"
                className="choice-pill"
                onClick={() => setForm({ ...form, preferred_days: [0, 1, 2, 3, 4] })}
              >
                Dias úteis
              </button>
              {DAY_OPTIONS.map((day) => (
                <button
                  key={day.value}
                  type="button"
                  className={`choice-pill${form.preferred_days.includes(day.value) ? " selected" : ""}`}
                  aria-pressed={form.preferred_days.includes(day.value)}
                  onClick={() => setForm({ ...form, preferred_days: toggleValue(form.preferred_days, day.value) })}
                >
                  {day.label}
                </button>
              ))}
            </div>
          </section>
        ) : null}

        {step === 3 ? (
          <section className="panel onboarding-step" aria-labelledby="onboarding-step-heading">
            <span className="section-kicker">Objetivo principal</span>
            <h2 id="onboarding-step-heading" className="panel-heading">Qual é uma meta importante para os próximos 30 dias?</h2>
            <FormField label="Meta de 30 dias" hint="Opcional, mas ajuda a personalizar sua campanha.">
              <TextInput
                maxLength={500}
                placeholder="Ex: Treinar 3 vezes por semana"
                value={form.main_goal}
                onChange={(event) => setForm({ ...form, main_goal: event.target.value })}
              />
            </FormField>
            <FormField label="Qual seria uma prova clara de progresso?" hint='Ex: "ler 1 capítulo", "treinar 3x", "guardar R$ 200".'>
              <TextInput
                maxLength={200}
                placeholder="Ex: treinar 3x por semana"
                value={form.progress_prompt}
                onChange={(event) => setForm({ ...form, progress_prompt: event.target.value })}
              />
            </FormField>
          </section>
        ) : null}

        {step === 4 ? (
          <section className="panel onboarding-step" aria-labelledby="onboarding-step-heading">
            <span className="section-kicker">Recompensas e tom</span>
            <h2 id="onboarding-step-heading" className="panel-heading">Que tipo de recompensa te motiva?</h2>
            <div className="choice-pill-row">
              {REWARD_STYLE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`choice-pill${form.reward_style === option.value ? " selected" : ""}`}
                  aria-pressed={form.reward_style === option.value}
                  onClick={() => setForm({ ...form, reward_style: option.value })}
                >
                  {option.label}
                </button>
              ))}
            </div>
            <h2 className="panel-heading">Você prefere missões leves ou desafiadoras?</h2>
            <div className="choice-pill-row">
              {INTENSITY_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`choice-pill${form.intensity === option.value ? " selected" : ""}`}
                  aria-pressed={form.intensity === option.value}
                  onClick={() => setForm({ ...form, intensity: option.value })}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </section>
        ) : null}

        <div className="composer-footer onboarding-footer">
          <span>Passo {step + 1} de 5</span>
          <div className="row-actions">
            {step > 0 ? <button className="button secondary" type="button" onClick={goBack} disabled={busy}>Voltar</button> : null}
            <button className="button primary" type="button" onClick={goNext} disabled={busy}>
              {step === 4 ? "Ver sugestões" : "Próximo"}
            </button>
          </div>
        </div>
      </>
    );
  }

  function renderMissionSuggestion(mission: MissionSuggestion) {
    const selected = selectedMissionKeys.includes(mission.key);
    return (
      <label key={mission.key} className={`suggestion-item${selected ? " selected" : ""}`}>
        <input
          type="checkbox"
          checked={selected}
          onChange={() => setSelectedMissionKeys((current) => toggleValue(current, mission.key))}
        />
        <span className="suggestion-body">
          <span className="suggestion-title">{mission.title}</span>
          <span className="suggestion-meta">{MISSION_TYPE_LABELS[mission.type]}</span>
          {mission.description ? <span className="suggestion-description">{mission.description}</span> : null}
        </span>
      </label>
    );
  }

  function renderRewardSuggestion(reward: RewardSuggestion) {
    const selected = selectedRewardKeys.includes(reward.key);
    return (
      <label key={reward.key} className={`suggestion-item${selected ? " selected" : ""}`}>
        <input
          type="checkbox"
          checked={selected}
          onChange={() => setSelectedRewardKeys((current) => toggleValue(current, reward.key))}
        />
        <span className="suggestion-body">
          <span className="suggestion-title">{reward.name}</span>
          <span className="suggestion-meta">{reward.cost} ouro</span>
        </span>
      </label>
    );
  }

  function renderConfirm() {
    if (!preview) return null;
    const dailyMissions = preview.missions.filter((mission) => mission.type === "daily");
    const weeklyMissions = preview.missions.filter((mission) => mission.type === "weekly");
    const campaignMissions = preview.missions.filter((mission) => mission.type === "long_term");

    return (
      <section className="panel onboarding-step" aria-labelledby="onboarding-confirm-heading">
        <span className="section-kicker">Revise sua aventura</span>
        <h2 id="onboarding-confirm-heading" className="panel-heading">Confirme suas missões e recompensas</h2>
        <p>Desmarque o que não quiser criar agora. Você pode ajustar depois em Missões.</p>

        <h3 className="panel-heading">Missões diárias</h3>
        <div className="suggestion-list">{dailyMissions.map(renderMissionSuggestion)}</div>

        <h3 className="panel-heading">Missão semanal</h3>
        <div className="suggestion-list">{weeklyMissions.map(renderMissionSuggestion)}</div>

        <h3 className="panel-heading">Campanha de 30 dias</h3>
        <div className="suggestion-list">{campaignMissions.map(renderMissionSuggestion)}</div>

        <h3 className="panel-heading">Recompensas sugeridas</h3>
        <div className="suggestion-list">{preview.rewards.map(renderRewardSuggestion)}</div>

        <div className="achievement-pop">
          <strong>Medalha ao concluir:</strong>
          <span className="achievement-pop-row"><GameIcon variant="medal" />{preview.class_badge.name}</span>
        </div>

        <div className="composer-footer onboarding-footer">
          <span>Você pode revisar tudo antes de começar.</span>
          <div className="row-actions">
            <button className="button secondary" type="button" onClick={goBack} disabled={busy}>Voltar</button>
            <button className="button primary" type="button" onClick={confirmOnboarding} disabled={busy}>
              Começar aventura
            </button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="view-page onboarding-page" aria-labelledby="onboarding-heading">
      <header className="view-hero">
        <span className="section-kicker">Bem-vindo(a)</span>
        <h1 className="page-heading" id="onboarding-heading">Crie seu herói</h1>
        <p>Responda algumas perguntas rápidas para receber missões e recompensas personalizadas.</p>
      </header>
      <div className="onboarding-layout">
        <div className="onboarding-main">
          {error ? <ErrorPanel>{error}</ErrorPanel> : null}
          {phase === "questions" ? renderQuestions() : renderConfirm()}
        </div>
        {renderHeroPreview()}
      </div>
    </section>
  );
}
