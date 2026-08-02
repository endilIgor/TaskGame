import { apiGet, apiPatch, apiPost } from "./api.js";
import type { Difficulty, Mission, MissionCreate, MissionType, MissionUpdate } from "./types.js";

type IsCurrent = () => boolean;

const days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"];

function element<K extends keyof HTMLElementTagNameMap>(
  tagName: K,
  className?: string,
  text?: string,
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Erro desconhecido";
}

function createSelect(name: string, values: readonly string[], label: string): HTMLLabelElement {
  const field = element("label", "form-field");
  field.append(element("span", "field-label", label));
  const select = element("select") as HTMLSelectElement;
  select.name = name;
  for (const value of values) {
    const option = element("option", undefined, value) as HTMLOptionElement;
    option.value = value;
    select.append(option);
  }
  field.append(select);
  return field;
}

function createMissionForm(root: HTMLElement, isCurrent: IsCurrent): HTMLElement {
  const form = element("form", "panel mission-form");
  form.append(element("h2", "panel-heading", "Nova missao"));

  const fields = element("div", "form-grid");
  const title = element("label", "form-field");
  title.append(element("span", "field-label", "Titulo"));
  const titleInput = element("input") as HTMLInputElement;
  titleInput.name = "title";
  titleInput.required = true;
  titleInput.maxLength = 120;
  title.append(titleInput);
  fields.append(title);

  const description = element("label", "form-field");
  description.append(element("span", "field-label", "Descricao"));
  const descriptionInput = element("textarea") as HTMLTextAreaElement;
  descriptionInput.name = "description";
  description.append(descriptionInput);
  fields.append(description);

  const type = createSelect("type", ["daily", "weekly", "long_term"], "Tipo");
  const difficulty = createSelect("difficulty", ["easy", "medium", "hard", "epic"], "Dificuldade");
  const category = element("label", "form-field");
  category.append(element("span", "field-label", "Categoria"));
  const categoryInput = element("input") as HTMLInputElement;
  categoryInput.name = "category";
  categoryInput.maxLength = 80;
  category.append(categoryInput);
  fields.append(type, difficulty, category);

  const startDate = element("label", "form-field");
  startDate.append(element("span", "field-label", "Data de inicio"));
  const startDateInput = element("input") as HTMLInputElement;
  startDateInput.name = "start_date";
  startDateInput.type = "date";
  startDateInput.value = new Date().toISOString().slice(0, 10);
  startDate.append(startDateInput);
  const targetDate = element("label", "form-field");
  targetDate.append(element("span", "field-label", "Data alvo"));
  const targetDateInput = element("input") as HTMLInputElement;
  targetDateInput.name = "target_date";
  targetDateInput.type = "date";
  targetDate.append(targetDateInput);
  fields.append(startDate, targetDate);

  const target = element("label", "form-field progress-target-field");
  target.append(element("span", "field-label", "Meta de progresso"));
  const targetInput = element("input") as HTMLInputElement;
  targetInput.name = "progress_target";
  targetInput.type = "number";
  targetInput.min = "1";
  targetInput.step = "1";
  target.append(targetInput);
  const current = element("label", "form-field progress-target-field");
  current.append(element("span", "field-label", "Progresso inicial"));
  const currentInput = element("input") as HTMLInputElement;
  currentInput.name = "progress_current";
  currentInput.type = "number";
  currentInput.min = "0";
  currentInput.step = "1";
  currentInput.value = "0";
  current.append(currentInput);
  fields.append(current, target);

  const repeatDays = element("fieldset", "repeat-days");
  repeatDays.append(element("legend", "field-label", "Dias de repeticao"));
  const dayOptions = element("div", "day-options");
  days.forEach((day, index) => {
    const option = element("label", "day-option");
    const checkbox = element("input") as HTMLInputElement;
    checkbox.type = "checkbox";
    checkbox.name = "repeat_days";
    checkbox.value = String(index);
    option.append(checkbox, document.createTextNode(day));
    dayOptions.append(option);
  });
  repeatDays.append(dayOptions);
  fields.append(repeatDays);

  const alert = element("p", "alert error");
  alert.hidden = true;
  const submit = element("button", "button primary", "Criar missao") as HTMLButtonElement;
  submit.type = "submit";
  form.append(fields, alert, submit);

  const typeSelect = type.querySelector("select");
  if (typeSelect === null) throw new Error("Mission type select was not created.");
  const syncTarget = (): void => {
    const isLongTerm = typeSelect.value === "long_term";
    target.hidden = !isLongTerm;
    current.hidden = !isLongTerm;
    targetInput.required = isLongTerm;
  };
  typeSelect.addEventListener("change", syncTarget);
  syncTarget();

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const missionType = data.get("type") as MissionType;
    const progressTarget = Number(data.get("progress_target"));
    const payload: MissionCreate = {
      title: String(data.get("title") ?? "").trim(),
      type: missionType,
      difficulty: data.get("difficulty") as Difficulty,
    };
    const categoryValue = String(data.get("category") ?? "").trim();
    if (categoryValue) payload.category = categoryValue;
    const descriptionValue = String(data.get("description") ?? "").trim();
    if (descriptionValue) payload.description = descriptionValue;
    const startDateValue = String(data.get("start_date") ?? "");
    if (startDateValue) payload.start_date = startDateValue;
    const targetDateValue = String(data.get("target_date") ?? "");
    if (targetDateValue) payload.target_date = targetDateValue;
    const repeatDaysValue = data.getAll("repeat_days").map((value) => Number(value));
    if (repeatDaysValue.length > 0) payload.repeat_days = repeatDaysValue;
    if (missionType === "long_term") {
      payload.progress_current = Number(data.get("progress_current"));
      payload.progress_target = progressTarget;
    }

    void (async () => {
      alert.hidden = true;
      submit.disabled = true;
      try {
        await apiPost<Mission>("/missions", payload);
        if (isCurrent()) await renderMissions(root, isCurrent);
      } catch (error) {
        if (isCurrent()) {
          alert.textContent = `Nao foi possivel criar a missao: ${errorMessage(error)}`;
          alert.hidden = false;
        }
      } finally {
        if (isCurrent()) submit.disabled = false;
      }
    })();
  });

  return form;
}

function missionMeta(mission: Mission): string {
  const category = mission.category ? ` | ${mission.category}` : "";
  const target = mission.target_date ? ` | alvo ${mission.target_date}` : "";
  return `${mission.status} | ${mission.type} | ${mission.difficulty}${category} | inicio ${mission.start_date}${target}`;
}


function createMissionEditForm(root: HTMLElement, mission: Mission, isCurrent: IsCurrent): HTMLElement {
  const details = element("details", "inline-editor");
  details.append(element("summary", undefined, "Editar"));
  const form = element("form", "compact-form");
  const fields = element("div", "form-grid");

  const title = element("label", "form-field");
  title.append(element("span", "field-label", "Titulo"));
  const titleInput = element("input") as HTMLInputElement;
  titleInput.name = "title";
  titleInput.required = true;
  titleInput.maxLength = 120;
  titleInput.value = mission.title;
  title.append(titleInput);

  const description = element("label", "form-field");
  description.append(element("span", "field-label", "Descricao"));
  const descriptionInput = element("textarea") as HTMLTextAreaElement;
  descriptionInput.name = "description";
  descriptionInput.value = mission.description ?? "";
  description.append(descriptionInput);

  const type = createSelect("type", ["daily", "weekly", "long_term"], "Tipo");
  const typeSelect = type.querySelector("select");
  if (typeSelect === null) throw new Error("Mission type select was not created.");
  typeSelect.value = mission.type;
  const difficulty = createSelect("difficulty", ["easy", "medium", "hard", "epic"], "Dificuldade");
  const difficultySelect = difficulty.querySelector("select");
  if (difficultySelect === null) throw new Error("Mission difficulty select was not created.");
  difficultySelect.value = mission.difficulty;

  const category = element("label", "form-field");
  category.append(element("span", "field-label", "Categoria"));
  const categoryInput = element("input") as HTMLInputElement;
  categoryInput.name = "category";
  categoryInput.maxLength = 80;
  categoryInput.value = mission.category ?? "";
  category.append(categoryInput);

  const start = element("label", "form-field");
  start.append(element("span", "field-label", "Data de inicio"));
  const startInput = element("input") as HTMLInputElement;
  startInput.name = "start_date";
  startInput.type = "date";
  startInput.required = true;
  startInput.value = mission.start_date;
  start.append(startInput);

  const target = element("label", "form-field");
  target.append(element("span", "field-label", "Data alvo"));
  const targetInput = element("input") as HTMLInputElement;
  targetInput.name = "target_date";
  targetInput.type = "date";
  targetInput.value = mission.target_date ?? "";
  target.append(targetInput);

  const progressTarget = element("label", "form-field");
  progressTarget.append(element("span", "field-label", "Meta de progresso"));
  const progressTargetInput = element("input") as HTMLInputElement;
  progressTargetInput.name = "progress_target";
  progressTargetInput.type = "number";
  progressTargetInput.min = "1";
  progressTargetInput.step = "1";
  progressTargetInput.value = mission.progress_target === null ? "" : String(mission.progress_target);
  progressTarget.append(progressTargetInput);

  const repeatDays = element("fieldset", "repeat-days");
  repeatDays.append(element("legend", "field-label", "Dias de repeticao"));
  const dayOptions = element("div", "day-options");
  days.forEach((day, index) => {
    const option = element("label", "day-option");
    const checkbox = element("input") as HTMLInputElement;
    checkbox.type = "checkbox";
    checkbox.name = "repeat_days";
    checkbox.value = String(index);
    checkbox.checked = mission.repeat_days?.includes(index) ?? false;
    option.append(checkbox, document.createTextNode(day));
    dayOptions.append(option);
  });
  repeatDays.append(dayOptions);
  fields.append(title, description, type, difficulty, category, start, target, progressTarget, repeatDays);

  const alert = element("p", "alert error");
  alert.hidden = true;
  const save = element("button", "button primary", "Salvar") as HTMLButtonElement;
  save.type = "submit";
  form.append(fields, alert, save);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const missionType = data.get("type") as MissionType;
    const payload: MissionUpdate = {
      title: String(data.get("title") ?? "").trim(),
      description: String(data.get("description") ?? "").trim() || null,
      type: missionType,
      difficulty: data.get("difficulty") as Difficulty,
      category: String(data.get("category") ?? "").trim() || null,
      start_date: String(data.get("start_date")),
      target_date: String(data.get("target_date") ?? "") || null,
      repeat_days: data.getAll("repeat_days").map((value) => Number(value)),
      progress_target: missionType === "long_term" ? Number(data.get("progress_target")) : null,
    };
    void (async () => {
      save.disabled = true;
      alert.hidden = true;
      try {
        await apiPatch<Mission>(`/missions/${mission.id}`, payload);
        if (isCurrent()) await renderMissions(root, isCurrent);
      } catch (error) {
        if (isCurrent()) {
          alert.textContent = `Nao foi possivel editar a missao: ${errorMessage(error)}`;
          alert.hidden = false;
        }
      } finally {
        if (isCurrent()) save.disabled = false;
      }
    })();
  });
  details.append(form);
  return details;
}


function createMissionList(root: HTMLElement, missions: Mission[], isCurrent: IsCurrent): HTMLElement {
  const panel = element("section", "panel");
  panel.append(element("h2", "panel-heading", "Missoes"));
  const list = element("div", "mission-list");
  if (missions.length === 0) {
    list.append(element("p", "empty-state", "Nenhuma missao encontrada."));
  }

  for (const mission of missions) {
    const item = element("article", "mission-row");
    const details = element("div", "mission-details");
    details.append(element("strong", "mission-title", mission.title), element("span", "mission-meta", missionMeta(mission)));
    if (mission.description) details.append(element("span", "mission-meta", mission.description));
    if (mission.type === "long_term" && mission.progress_target !== null) {
      details.append(element("span", "mission-meta", `${mission.progress_current} / ${mission.progress_target} progresso`));
    }
    const actions = element("div", "row-actions");
    if (mission.status === "active" && mission.type !== "long_term") {
      const complete = element("button", "button", "Concluir") as HTMLButtonElement;
      complete.type = "button";
      complete.addEventListener("click", () => {
        void runMissionAction(root, isCurrent, complete, `/missions/${mission.id}/complete`);
      });
      actions.append(complete);
    }
    if (mission.status === "active" && mission.type === "long_term") {
      const progress = element("button", "button secondary", "+1 progresso") as HTMLButtonElement;
      progress.type = "button";
      progress.addEventListener("click", () => {
        void runMissionAction(root, isCurrent, progress, `/missions/${mission.id}/progress`, { amount: 1 });
      });
      actions.append(progress);
    }
    if (mission.status !== "archived") {
      const archive = element("button", "button danger", "Arquivar") as HTMLButtonElement;
      archive.type = "button";
      archive.addEventListener("click", () => {
        void runMissionAction(root, isCurrent, archive, `/missions/${mission.id}/archive`);
      });
      actions.append(archive);
    }
    details.append(createMissionEditForm(root, mission, isCurrent));
    item.append(details, actions);
    list.append(item);
  }
  panel.append(list);
  return panel;
}

async function runMissionAction(
  root: HTMLElement,
  isCurrent: IsCurrent,
  button: HTMLButtonElement,
  path: string,
  body?: unknown,
): Promise<void> {
  button.disabled = true;
  try {
    await apiPost(path, body);
    if (isCurrent()) await renderMissions(root, isCurrent);
  } catch (error) {
    if (isCurrent()) {
      root.replaceChildren(element("section", "error-panel", `Nao foi possivel atualizar a missao: ${errorMessage(error)}`));
    }
  } finally {
    if (isCurrent()) button.disabled = false;
  }
}


function createMissionFilters(
  missions: Mission[],
  onFilter: (missions: Mission[]) => void,
): HTMLElement {
  const panel = element("section", "panel filter-panel");
  panel.append(element("h2", "panel-heading", "Filtros"));
  const fields = element("div", "form-grid");
  const search = element("label", "form-field");
  search.append(element("span", "field-label", "Buscar"));
  const searchInput = element("input") as HTMLInputElement;
  searchInput.type = "search";
  searchInput.placeholder = "Titulo, descricao ou categoria";
  search.append(searchInput);
  const type = createSelect("filter_type", ["all", "daily", "weekly", "long_term"], "Tipo");
  const status = createSelect("filter_status", ["all", "active", "completed", "archived"], "Status");
  fields.append(search, type, status);
  panel.append(fields);

  const typeSelect = type.querySelector("select");
  const statusSelect = status.querySelector("select");
  if (typeSelect === null || statusSelect === null) throw new Error("Mission filters were not created.");
  const apply = (): void => {
    const query = searchInput.value.trim().toLowerCase();
    onFilter(missions.filter((mission) => {
      const searchable = `${mission.title} ${mission.description ?? ""} ${mission.category ?? ""}`.toLowerCase();
      return (typeSelect.value === "all" || mission.type === typeSelect.value)
        && (statusSelect.value === "all" || mission.status === statusSelect.value)
        && (!query || searchable.includes(query));
    }));
  };
  searchInput.addEventListener("input", apply);
  typeSelect.addEventListener("change", apply);
  statusSelect.addEventListener("change", apply);
  return panel;
}


export async function renderMissions(root: HTMLElement, isCurrent: IsCurrent = () => true): Promise<void> {
  if (isCurrent()) root.replaceChildren(element("p", "empty-state", "Carregando missoes..."));
  try {
    const missions = await apiGet<Mission[]>("/missions?include_archived=true");
    if (!isCurrent()) return;
    const page = element("section", "view-page");
    const listHost = element("div");
    const showMissions = (filtered: Mission[]): void => {
      listHost.replaceChildren(createMissionList(root, filtered, isCurrent));
    };
    page.append(
      element("h1", "page-heading", "Missoes"),
      createMissionForm(root, isCurrent),
      createMissionFilters(missions, showMissions),
      listHost,
    );
    showMissions(missions);
    root.replaceChildren(page);
  } catch (error) {
    if (isCurrent()) root.replaceChildren(element("section", "error-panel", `Nao foi possivel carregar as missoes: ${errorMessage(error)}`));
  }
}

export async function renderGoals(root: HTMLElement, isCurrent: IsCurrent = () => true): Promise<void> {
  if (isCurrent()) root.replaceChildren(element("p", "empty-state", "Carregando objetivos..."));
  try {
    const goals = await apiGet<Array<Mission & { progress_percent: number }>>("/goals");
    if (!isCurrent()) return;
    const page = element("section", "view-page");
    page.append(element("h1", "page-heading", "Objetivos"));
    const list = element("section", "goal-list");
    if (goals.length === 0) list.append(element("p", "empty-state", "Nenhum objetivo de longo prazo."));
    for (const goal of goals) {
      const item = element("article", "goal-row");
      const header = element("div", "goal-heading");
      header.append(element("strong", "mission-title", goal.title), element("span", "goal-percent", `${goal.progress_percent}%`));
      const track = element("div", "progress-track");
      const bar = element("div", "progress-bar");
      bar.style.width = `${goal.progress_percent}%`;
      track.append(bar);
      item.append(header, track, element("span", "mission-meta", `${goal.progress_current} / ${goal.progress_target} progresso`));
      list.append(item);
    }
    page.append(list);
    root.replaceChildren(page);
  } catch (error) {
    if (isCurrent()) root.replaceChildren(element("section", "error-panel", `Nao foi possivel carregar os objetivos: ${errorMessage(error)}`));
  }
}
