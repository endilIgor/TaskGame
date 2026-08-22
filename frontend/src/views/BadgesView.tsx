import { apiGet } from "../api/client";
import { BadgeTile } from "../components/BadgeTile";
import { GameIcon } from "../components/GameIcon";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { BadgeStatus } from "../types";

export function BadgesView() {
  const badges = useAsyncData(() => apiGet<BadgeStatus[]>("/badges"), []);

  if (badges.status === "loading") return <LoadingPanel />;
  if (badges.status === "error") return <ErrorPanel>{badges.error}</ErrorPanel>;

  const earned = badges.data.filter((badge) => badge.earned).length;

  return (
    <section className="view-page achievements-page" aria-labelledby="badges-heading">
      <header className="view-hero achievements-hero">
        <span className="section-kicker">Conquistas</span>
        <h1 className="page-heading" id="badges-heading">Hall de conquistas</h1>
        <p>Metas desbloqueadas ganham destaque dourado; as bloqueadas mostram o próximo feito a perseguir.</p>
      </header>
      <div className="achievement-summary panel">
        <span className="badge-emblem" aria-hidden="true"><GameIcon variant="medal" /></span>
        <div>
          <span className="section-kicker">Progresso</span>
          <h2 className="panel-heading">{earned}/{badges.data.length} conquistas liberadas</h2>
        </div>
      </div>
      {badges.data.length ? <div className="badge-grid achievement-grid">{badges.data.map((badge) => <BadgeTile badge={badge} key={badge.id} />)}</div> : <EmptyState>Nenhuma conquista configurada.</EmptyState>}
    </section>
  );
}
