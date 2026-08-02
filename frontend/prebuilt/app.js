import { renderDashboard } from "./dashboard.js";
import { renderMissions, renderGoals } from "./missions.js";
import { renderBadges } from "./badges.js";
import { renderRewards } from "./rewards.js";
import { renderReports } from "./reports.js";
import { renderBackup } from "./backup.js";
const viewTitles = {
    dashboard: "Dashboard",
    missions: "Missoes",
    goals: "Objetivos",
    badges: "Medalhas",
    rewards: "Loja",
    reports: "Relatorio",
    backup: "Backup",
};
const renderers = {
    dashboard: renderDashboard,
    missions: renderMissions,
    goals: renderGoals,
    badges: renderBadges,
    rewards: renderRewards,
    reports: renderReports,
    backup: renderBackup,
};
let currentNavigation = 0;
async function navigate(root, view) {
    const navigation = ++currentNavigation;
    const renderer = renderers[view];
    if (renderer !== undefined)
        await renderer(root, () => navigation === currentNavigation);
}
const root = document.querySelector("#app");
const navigationButtons = document.querySelectorAll(".nav-button");
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
//# sourceMappingURL=app.js.map
