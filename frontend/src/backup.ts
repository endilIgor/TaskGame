type IsCurrent = () => boolean;

function downloadLink(href: string, text: string): HTMLAnchorElement {
  const link = document.createElement("a");
  link.className = "button";
  link.href = href;
  link.textContent = text;
  return link;
}

export async function renderBackup(root: HTMLElement, isCurrent: IsCurrent = () => true): Promise<void> {
  if (!isCurrent()) return;
  const page = document.createElement("section");
  page.className = "view-page";
  const heading = document.createElement("h1");
  heading.className = "page-heading";
  heading.textContent = "Backup";
  const panel = document.createElement("section");
  panel.className = "panel backup-panel";
  const title = document.createElement("h2");
  title.className = "panel-heading";
  title.textContent = "Exportar dados";
  const actions = document.createElement("div");
  actions.className = "backup-actions";
  actions.append(
    downloadLink("/api/backup/export.json", "JSON"),
    downloadLink("/api/backup/missions.csv", "Missoes CSV"),
    downloadLink("/api/backup/completions.csv", "Conclusoes CSV"),
  );
  panel.append(title, actions);
  page.append(heading, panel);
  root.replaceChildren(page);
}
