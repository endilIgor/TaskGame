import { renderDashboard } from "./dashboard.js";

const viewTitles: Record<string, string> = {
  dashboard: "Dashboard",
  missions: "Missoes",
  goals: "Objetivos",
  badges: "Medalhas",
  rewards: "Loja",
  reports: "Relatorio",
  backup: "Backup",
};

function renderPlaceholder(root: HTMLElement, title: string): void {
  const panel = document.createElement("section");
  panel.className = "panel";
  const heading = document.createElement("h1");
  heading.className = "page-heading";
  heading.textContent = title;
  panel.append(heading);
  root.replaceChildren(panel);
}

async function navigate(root: HTMLElement, view: string): Promise<void> {
  if (view === "dashboard") {
    await renderDashboard(root);
    return;
  }
  renderPlaceholder(root, viewTitles[view]);
}

const root = document.querySelector<HTMLElement>("#app");
const navigationButtons = document.querySelectorAll<HTMLButtonElement>(".nav-button");

if (root === null) {
  throw new Error("TaskGame app root was not found.");
}

for (const button of navigationButtons) {
  button.addEventListener("click", () => {
    const view = button.dataset.view;
    if (view === undefined || viewTitles[view] === undefined) {
      return;
    }
    for (const navigationButton of navigationButtons) {
      navigationButton.classList.toggle("active", navigationButton === button);
    }
    root.focus();
    void navigate(root, view);
  });
}

void navigate(root, "dashboard");
