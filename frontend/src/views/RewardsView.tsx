import { useState } from "react";
import { apiGet, apiPost } from "../api/client";
import { FormField, TextArea, TextInput } from "../components/FormControls";
import { GameIcon } from "../components/GameIcon";
import { RewardCard } from "../components/RewardCard";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { Reward, RewardCreatePayload, RewardPurchase, RewardSuggestion } from "../types";

export function RewardsView() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [cost, setCost] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | "create" | `suggestion:${string}` | null>(null);
  const rewards = useAsyncData(() => apiGet<Reward[]>("/rewards"), [refreshKey]);
  const purchases = useAsyncData(() => apiGet<RewardPurchase[]>("/rewards/purchases"), [refreshKey]);
  const suggestions = useAsyncData(() => apiGet<RewardSuggestion[]>("/rewards/suggestions"), [refreshKey]);

  async function create(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy("create");
    setError(null);
    try {
      await apiPost<Reward, RewardCreatePayload>("/rewards", {
        name: name.trim(),
        description: description.trim() || null,
        cost: Number(cost),
      });
      setName("");
      setDescription("");
      setCost("");
      setRefreshKey((key) => key + 1);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível criar a recompensa.");
    } finally {
      setBusy(null);
    }
  }

  async function purchase(reward: Reward) {
    if (!window.confirm(`Comprar "${reward.name}" por ${reward.cost} ouro?`)) return;
    setBusy(reward.id);
    setError(null);
    try {
      await apiPost<RewardPurchase>(`/rewards/${reward.id}/purchase`);
      setRefreshKey((key) => key + 1);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Compra indisponível.");
    } finally {
      setBusy(null);
    }
  }

  async function createSuggestedReward(suggestion: RewardSuggestion) {
    setBusy(`suggestion:${suggestion.key}`);
    setError(null);
    try {
      await apiPost<Reward, RewardCreatePayload>("/rewards", {
        name: suggestion.name,
        description: suggestion.description,
        cost: suggestion.cost,
      });
      setRefreshKey((key) => key + 1);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível adicionar a sugestão à loja.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="view-page" aria-labelledby="rewards-heading">
      <header><span className="section-kicker">Ouro</span><h1 className="page-heading" id="rewards-heading">Loja</h1></header>
      <form className="panel reward-form" onSubmit={create}>
        <div className="section-heading">
          <div>
            <span className="section-kicker">Prateleira da guilda</span>
            <h2 className="panel-heading">Nova recompensa</h2>
          </div>
          <span className="section-count"><GameIcon variant="coin" /></span>
        </div>
        <div className="reward-composer-grid">
          <FormField className="field-reward-name" label="Nome" hint="O prêmio que você quer desbloquear."><TextInput required maxLength={120} placeholder="Ex: Noite de cinema" value={name} onChange={(event) => setName(event.target.value)} /></FormField>
          <FormField className="field-reward-description" label="Descrição" hint="Detalhe a regra ou contexto da recompensa."><TextArea maxLength={500} placeholder="Ex: Assistir um filme sem culpa depois das missões do dia." value={description} onChange={(event) => setDescription(event.target.value)} /></FormField>
          <FormField className="field-reward-cost" label="Custo em ouro" hint="Valor mínimo: 1 ouro."><TextInput required type="number" min="1" placeholder="50" value={cost} onChange={(event) => setCost(event.target.value)} /></FormField>
        </div>
        <div className="composer-footer"><span>Use a loja para trocar ouro por recompensas reais.</span><button className="button primary" disabled={busy === "create"}>Adicionar recompensa</button></div>
      </form>
      {error ? <ErrorPanel>{error}</ErrorPanel> : null}
      {suggestions.status === "error" ? <ErrorPanel>{suggestions.error}</ErrorPanel> : null}
      {suggestions.status === "ready" && suggestions.data.length ? (
        <section className="panel">
          <div className="section-heading">
            <div>
              <span className="section-kicker">Compras inteligentes</span>
              <h2 className="panel-heading">Sugestões por missões e medalhas</h2>
            </div>
            <span className="section-count"><GameIcon variant="medal" /></span>
          </div>
          <div className="reward-grid">
            {suggestions.data.map((suggestion) => (
              <article className="reward-tile" key={suggestion.key}>
                <span className="section-kicker">{suggestion.source_label}</span>
                <h2 className="reward-name">{suggestion.name}</h2>
                <p className="quest-description">{suggestion.description}</p>
                <div className="reward-footer">
                  <strong className="reward-cost">{suggestion.cost} ouro</strong>
                  <button className="button secondary" type="button" onClick={() => createSuggestedReward(suggestion)} disabled={busy === `suggestion:${suggestion.key}`}>Adicionar à loja</button>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}
      {rewards.status === "loading" ? <LoadingPanel /> : null}
      {rewards.status === "error" ? <ErrorPanel>{rewards.error}</ErrorPanel> : null}
      {rewards.status === "ready" ? rewards.data.length ? (
        <div className="reward-grid">
          {rewards.data.map((reward) => <RewardCard reward={reward} key={reward.id} onPurchase={purchase} busy={busy === reward.id} />)}
        </div>
      ) : <EmptyState>Nenhuma recompensa à venda.</EmptyState> : null}
      {purchases.status === "error" ? <ErrorPanel>{purchases.error}</ErrorPanel> : null}
      {purchases.status === "ready" ? (
        <section className="panel">
          <h2 className="panel-heading">Histórico de compras</h2>
          <div className="history-list">
            {purchases.data.length ? purchases.data.map((purchase) => (
              <div className="history-row" key={purchase.id}>
                <span>Recompensa #{purchase.reward_id}</span>
                <span>{purchase.cost_paid} ouro</span>
                <time>{new Date(purchase.purchased_at).toLocaleString("pt-BR")}</time>
              </div>
            )) : <EmptyState>Nenhuma compra registrada.</EmptyState>}
          </div>
        </section>
      ) : null}
    </section>
  );
}
