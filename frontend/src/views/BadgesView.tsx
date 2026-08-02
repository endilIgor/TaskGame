import { apiGet } from "../api/client";
import { BadgeTile } from "../components/BadgeTile";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { BadgeStatus } from "../types";

export function BadgesView() { const badges = useAsyncData(() => apiGet<BadgeStatus[]>("/badges"), []); return <section className="view-page" aria-labelledby="badges-heading"><header><span className="section-kicker">Conquistas</span><h1 className="page-heading" id="badges-heading">Medalhas</h1></header>{badges.status === "loading" ? <LoadingPanel /> : null}{badges.status === "error" ? <ErrorPanel>{badges.error}</ErrorPanel> : null}{badges.status === "ready" ? badges.data.length ? <div className="badge-grid">{badges.data.map((badge) => <BadgeTile badge={badge} key={badge.id} />)}</div> : <EmptyState>Nenhuma medalha configurada.</EmptyState> : null}</section>; }
