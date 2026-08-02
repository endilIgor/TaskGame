import { apiGet, apiPost } from "./api.js";
const days = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"];
function element(tagName, className, text) {
    const node = document.createElement(tagName);
    if (className)
        node.className = className;
    if (text !== undefined)
        node.textContent = text;
    return node;
}
function errorMessage(error) {
    return error instanceof Error ? error.message : "Erro desconhecido";
}
function createSelect(name, values, label) {
    const field = element("label", "form-field");
    field.append(element("span", "field-label", label));
    const select = element("select");
    select.name = name;
    for (const value of values) {
        const option = element("option", undefined, value);
        option.value = value;
        select.append(option);
    }
    field.append(select);
    return field;
}
function createMissionForm(root, isCurrent) {
    const form = element("form", "panel mission-form");
    form.append(element("h2", "panel-heading", "Nova missao"));
    const fields = element("div", "form-grid");
    const title = element("label", "form-field");
    title.append(element("span", "field-label", "Titulo"));
    const titleInput = element("input");
    titleInput.name = "title";
    titleInput.required = true;
    titleInput.maxLength = 120;
    title.append(titleInput);
    fields.append(title);
    const type = createSelect("type", ["daily", "weekly", "long_term"], "Tipo");
    const difficulty = createSelect("difficulty", ["easy", "medium", "hard", "epic"], "Dificuldade");
    const category = element("label", "form-field");
    category.append(element("span", "field-label", "Categoria"));
    const categoryInput = element("input");
    categoryInput.name = "category";
    categoryInput.maxLength = 80;
    category.append(categoryInput);
    fields.append(type, difficulty, category);
    const target = element("label", "form-field progress-target-field");
    target.append(element("span", "field-label", "Meta de progresso"));
    const targetInput = element("input");
    targetInput.name = "progress_target";
    targetInput.type = "number";
    targetInput.min = "1";
    targetInput.step = "1";
    target.append(targetInput);
    fields.append(target);
    const repeatDays = element("fieldset", "repeat-days");
    repeatDays.append(element("legend", "field-label", "Dias de repeticao"));
    const dayOptions = element("div", "day-options");
    days.forEach((day, index) => {
        const option = element("label", "day-option");
        const checkbox = element("input");
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
    const submit = element("button", "button primary", "Criar missao");
    submit.type = "submit";
    form.append(fields, alert, submit);
    const typeSelect = type.querySelector("select");
    if (typeSelect === null)
        throw new Error("Mission type select was not created.");
    const syncTarget = () => {
        const isLongTerm = typeSelect.value === "long_term";
        target.hidden = !isLongTerm;
        targetInput.required = isLongTerm;
    };
    typeSelect.addEventListener("change", syncTarget);
    syncTarget();
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const data = new FormData(form);
        const missionType = data.get("type");
        const progressTarget = Number(data.get("progress_target"));
        const payload = {
            title: String(data.get("title") ?? "").trim(),
            type: missionType,
            difficulty: data.get("difficulty"),
        };
        const categoryValue = String(data.get("category") ?? "").trim();
        if (categoryValue)
            payload.category = categoryValue;
        const repeatDaysValue = data.getAll("repeat_days").map((value) => Number(value));
        if (repeatDaysValue.length > 0)
            payload.repeat_days = repeatDaysValue;
        if (missionType === "long_term")
            payload.progress_target = progressTarget;
        void (async () => {
            alert.hidden = true;
            submit.disabled = true;
            try {
                await apiPost("/missions", payload);
                if (isCurrent())
                    await renderMissions(root, isCurrent);
            }
            catch (error) {
                if (isCurrent()) {
                    alert.textContent = `Nao foi possivel criar a missao: ${errorMessage(error)}`;
                    alert.hidden = false;
                }
            }
            finally {
                if (isCurrent())
                    submit.disabled = false;
            }
        })();
    });
    return form;
}
function missionMeta(mission) {
    const category = mission.category ? ` | ${mission.category}` : "";
    return `${mission.type} | ${mission.difficulty}${category}`;
}
function createMissionList(root, missions, isCurrent) {
    const panel = element("section", "panel");
    panel.append(element("h2", "panel-heading", "Missoes ativas"));
    const list = element("div", "mission-list");
    if (missions.length === 0) {
        list.append(element("p", "empty-state", "Nenhuma missao ativa."));
    }
    for (const mission of missions) {
        const item = element("article", "mission-row");
        const details = element("div", "mission-details");
        details.append(element("strong", "mission-title", mission.title), element("span", "mission-meta", missionMeta(mission)));
        if (mission.type === "long_term" && mission.progress_target !== null) {
            details.append(element("span", "mission-meta", `${mission.progress_current} / ${mission.progress_target} progresso`));
        }
        const actions = element("div", "row-actions");
        const complete = element("button", "button", "Concluir");
        complete.type = "button";
        complete.addEventListener("click", () => {
            void runMissionAction(root, isCurrent, complete, `/missions/${mission.id}/complete`);
        });
        actions.append(complete);
        if (mission.type === "long_term") {
            const progress = element("button", "button secondary", "+1 progresso");
            progress.type = "button";
            progress.addEventListener("click", () => {
                void runMissionAction(root, isCurrent, progress, `/missions/${mission.id}/progress`, { amount: 1 });
            });
            actions.append(progress);
        }
        item.append(details, actions);
        list.append(item);
    }
    panel.append(list);
    return panel;
}
async function runMissionAction(root, isCurrent, button, path, body) {
    button.disabled = true;
    try {
        await apiPost(path, body);
        if (isCurrent())
            await renderMissions(root, isCurrent);
    }
    catch (error) {
        if (isCurrent()) {
            root.replaceChildren(element("section", "error-panel", `Nao foi possivel atualizar a missao: ${errorMessage(error)}`));
        }
    }
    finally {
        if (isCurrent())
            button.disabled = false;
    }
}
export async function renderMissions(root, isCurrent = () => true) {
    if (isCurrent())
        root.replaceChildren(element("p", "empty-state", "Carregando missoes..."));
    try {
        const missions = await apiGet("/missions");
        if (!isCurrent())
            return;
        const activeMissions = missions.filter((mission) => mission.status === "active");
        const page = element("section", "view-page");
        page.append(element("h1", "page-heading", "Missoes"), createMissionForm(root, isCurrent), createMissionList(root, activeMissions, isCurrent));
        root.replaceChildren(page);
    }
    catch (error) {
        if (isCurrent())
            root.replaceChildren(element("section", "error-panel", `Nao foi possivel carregar as missoes: ${errorMessage(error)}`));
    }
}
export async function renderGoals(root, isCurrent = () => true) {
    if (isCurrent())
        root.replaceChildren(element("p", "empty-state", "Carregando objetivos..."));
    try {
        const goals = await apiGet("/goals");
        if (!isCurrent())
            return;
        const page = element("section", "view-page");
        page.append(element("h1", "page-heading", "Objetivos"));
        const list = element("section", "goal-list");
        if (goals.length === 0)
            list.append(element("p", "empty-state", "Nenhum objetivo de longo prazo."));
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
    }
    catch (error) {
        if (isCurrent())
            root.replaceChildren(element("section", "error-panel", `Nao foi possivel carregar os objetivos: ${errorMessage(error)}`));
    }
}
//# sourceMappingURL=missions.js.map
