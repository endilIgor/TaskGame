import type { Reward } from "../types";

interface RewardCardProps {
  reward: Reward;
  onPurchase: (reward: Reward) => void;
  busy?: boolean;
}

export function RewardCard({ reward, onPurchase, busy = false }: RewardCardProps) {
  return (
    <article className={`reward-tile${reward.status !== "active" ? " archived" : ""}`}>
      <span className="section-kicker">Loja da guilda</span>
      <h2 className="reward-name">{reward.name}</h2>
      <p className="quest-description">{reward.description || "Uma recompensa reservada para sua jornada."}</p>
      <div className="reward-footer">
        <strong className="reward-cost">{reward.cost} ouro</strong>
        {reward.status === "active" ? <button className="button secondary" type="button" onClick={() => onPurchase(reward)} disabled={busy}>Comprar</button> : <span className="badge-status">Arquivada</span>}
      </div>
    </article>
  );
}
