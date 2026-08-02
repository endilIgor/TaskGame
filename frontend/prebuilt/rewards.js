import { apiGet, apiPatch, apiPost } from "./api.js";
function element                                       (tagName   , className         , text         )                           {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function errorMessage(error         )         {
  return error instanceof Error ? error.message : "Erro desconhecido";
}
function createRewardForm(root             , isCurrent           )              {
  const form = element("form", "panel reward-form");
  form.append(element("h2", "panel-heading", "Nova recompensa"));
  const fields = element("div", "form-grid");
  const name = element("label", "form-field");
  name.append(element("span", "field-label", "Nome"));
  const nameInput = element("input")                    ;
  nameInput.name = "name";
  nameInput.maxLength = 120;
  nameInput.required = true;
  name.append(nameInput);
  const description = element("label", "form-field");
  description.append(element("span", "field-label", "Descricao"));
  const descriptionInput = element("textarea")                       ;
  descriptionInput.name = "description";
  descriptionInput.maxLength = 500;
  description.append(descriptionInput);
  const cost = element("label", "form-field");
  cost.append(element("span", "field-label", "Custo em ouro"));
  const costInput = element("input")                    ;
  costInput.name = "cost";
  costInput.type = "number";
  costInput.min = "1";
  costInput.step = "1";
  costInput.required = true;
  cost.append(costInput);
  fields.append(name, description, cost);
  const alert = element("p", "alert error");
  alert.hidden = true;
  const submit = element("button", "button primary", "Criar recompensa")                     ;
  submit.type = "submit";
  form.append(fields, alert, submit);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const payload               = {
      name: String(data.get("name") ?? "").trim(),
      cost: Number(data.get("cost")),
    };
    const descriptionValue = String(data.get("description") ?? "").trim();
    if (descriptionValue) payload.description = descriptionValue;
    void (async () => {
      alert.hidden = true;
      submit.disabled = true;
      try {
        await apiPost        ("/rewards", payload);
        if (isCurrent()) await renderRewards(root, isCurrent);
      } catch (error) {
        if (isCurrent()) {
          alert.textContent = `Nao foi possivel criar a recompensa: ${errorMessage(error)}`;
          alert.hidden = false;
        }
      } finally {
        if (isCurrent()) submit.disabled = false;
      }
    })();
  });
  return form;
}
function createRewardEditForm(root             , reward        , isCurrent           )              {
  const details = element("details", "inline-editor");
  details.append(element("summary", undefined, "Editar"));
  const form = element("form", "compact-form");
  const name = element("input")                    ;
  name.required = true;
  name.maxLength = 120;
  name.value = reward.name;
  const description = element("textarea")                       ;
  description.maxLength = 500;
  description.value = reward.description ?? "";
  const cost = element("input")                    ;
  cost.type = "number";
  cost.min = "1";
  cost.required = true;
  cost.value = String(reward.cost);
  const alert = element("p", "alert error");
  alert.hidden = true;
  const save = element("button", "button primary", "Salvar")                     ;
  save.type = "submit";
  form.append(name, description, cost, alert, save);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const payload               = {
      name: name.value.trim(),
      description: description.value.trim(),
      cost: Number(cost.value),
    };
    void (async () => {
      save.disabled = true;
      alert.hidden = true;
      try {
        await apiPatch        (`/rewards/${reward.id}`, payload);
        if (isCurrent()) await renderRewards(root, isCurrent);
      } catch (error) {
        if (isCurrent()) {
          alert.textContent = `Nao foi possivel editar: ${errorMessage(error)}`;
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
function createRewardList(root             , rewards          , isCurrent           )              {
  const section = element("section", "reward-grid");
  if (rewards.length === 0) section.append(element("p", "empty-state", "Nenhuma recompensa cadastrada."));
  for (const reward of rewards) {
    const tile = element("article", "reward-tile");
    const alert = element("p", "alert error");
    alert.hidden = true;
    const actions = element("div", "row-actions");
    if (reward.status === "active") {
      const purchase = element("button", "button", "Comprar")                     ;
      purchase.type = "button";
      purchase.addEventListener("click", () => {
        void (async () => {
          alert.hidden = true;
          purchase.disabled = true;
          try {
            await apiPost(`/rewards/${reward.id}/purchase`);
            if (isCurrent()) await renderRewards(root, isCurrent);
          } catch (error) {
            if (isCurrent()) {
              alert.textContent = `Compra indisponivel: ${errorMessage(error)}`;
              alert.hidden = false;
            }
          } finally {
            if (isCurrent()) purchase.disabled = false;
          }
        })();
      });
      const archive = element("button", "button danger", "Arquivar")                     ;
      archive.type = "button";
      archive.addEventListener("click", () => {
        void (async () => {
          archive.disabled = true;
          try {
            await apiPost(`/rewards/${reward.id}/archive`);
            if (isCurrent()) await renderRewards(root, isCurrent);
          } catch (error) {
            if (isCurrent()) {
              alert.textContent = `Nao foi possivel arquivar: ${errorMessage(error)}`;
              alert.hidden = false;
            }
          } finally {
            if (isCurrent()) archive.disabled = false;
          }
        })();
      });
      actions.append(purchase, archive);
    }
    tile.append(
      element("strong", "reward-name", reward.name),
      element("p", "mission-meta", reward.description ?? "Sem descricao."),
      element("span", "reward-cost", `${reward.cost} ouro`),
      element("span", "mission-meta", reward.status),
      alert,
      createRewardEditForm(root, reward, isCurrent),
      actions,
    );
    section.append(tile);
  }
  return section;
}
function createPurchaseHistory(purchases                  , rewards          )              {
  const panel = element("section", "panel");
  panel.append(element("h2", "panel-heading", "Historico de compras"));
  const names = new Map(rewards.map((reward) => [reward.id, reward.name]));
  const list = element("div", "history-list");
  if (purchases.length === 0) list.append(element("p", "empty-state", "Nenhuma compra registrada."));
  for (const purchase of purchases) {
    const row = element("div", "history-row");
    row.append(
      element("strong", undefined, names.get(purchase.reward_id) ?? `Recompensa #${purchase.reward_id}`),
      element("span", "mission-meta", `${purchase.cost_paid} ouro | ${new Date(purchase.purchased_at).toLocaleString("pt-BR")}`),
    );
    list.append(row);
  }
  panel.append(list);
  return panel;
}
export async function renderRewards(root             , isCurrent            = () => true)                {
  if (isCurrent()) root.replaceChildren(element("p", "empty-state", "Carregando recompensas..."));
  try {
    const [rewards, purchases] = await Promise.all([
      apiGet          ("/rewards?include_archived=true"),
      apiGet                  ("/rewards/purchases"),
    ]);
    if (!isCurrent()) return;
    const page = element("section", "view-page");
    page.append(
      element("h1", "page-heading", "Loja"),
      createRewardForm(root, isCurrent),
      createRewardList(root, rewards, isCurrent),
      createPurchaseHistory(purchases, rewards),
    );
    root.replaceChildren(page);
  } catch (error) {
    if (isCurrent()) root.replaceChildren(element("section", "error-panel", `Nao foi possivel carregar as recompensas: ${errorMessage(error)}`));
  }
}
