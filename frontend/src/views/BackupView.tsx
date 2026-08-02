import { apiGet } from "../api/client";
import { ErrorPanel, LoadingPanel } from "../components/StatePanels";
import { useAsyncData } from "../hooks/useAsyncData";
import type { BackupStatus } from "../types";

export function BackupView() {
  const status = useAsyncData(() => apiGet<BackupStatus>("/backup/status"), []);
  if (status.status === "loading") return <LoadingPanel />;
  if (status.status === "error") return <ErrorPanel>{status.error}</ErrorPanel>;
  const dump = status.data;
  return <section className="view-page" aria-labelledby="backup-heading"><header><span className="section-kicker">Dados</span><h1 className="page-heading" id="backup-heading">Arquivo</h1></header><section className="panel backup-panel" data-liquid-ignore><h2 className="panel-heading">Exportar dados</h2><p className="quest-description">Arquivos portaveis para guardar a historia da sua guilda.</p><div className="backup-actions"><a className="button primary" href="/api/backup/export.json">Backup JSON</a><a className="button" href="/api/backup/missions.csv">Missoes CSV</a><a className="button" href="/api/backup/completions.csv">Conclusoes CSV</a></div></section><section className="panel glass-panel"><span className="liquid-glass-surface" aria-hidden="true" /><h2 className="panel-heading">Ultimo dump MySQL</h2>{dump.last_mysql_dump_at ? <dl className="weekly-stats"><div><dt>Arquivo</dt><dd>{dump.last_mysql_dump_filename || "Arquivo desconhecido"}</dd></div><div><dt>Gerado em</dt><dd>{new Date(dump.last_mysql_dump_at).toLocaleString("pt-BR")}</dd></div></dl> : <p className="empty-state">Nenhum dump MySQL encontrado.</p>}</section></section>;
}
