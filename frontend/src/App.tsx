import { DashboardView } from "./views/DashboardView";
import { MissionsView } from "./views/MissionsView";
import { JournalView } from "./views/JournalView";
import { GoalsView } from "./views/GoalsView";
import { BadgesView } from "./views/BadgesView";
import { RewardsView } from "./views/RewardsView";
import { ReportsView } from "./views/ReportsView";
import { AppShell } from "./components/AppShell";
import type { ReactNode } from "react";
import type { ViewKey } from "./types";

const views: Record<ViewKey, () => ReactNode> = {
  dashboard: () => <DashboardView />,
  missions: () => <MissionsView />,
  journal: () => <JournalView />,
  goals: () => <GoalsView />,
  badges: () => <BadgesView />,
  rewards: () => <RewardsView />,
  reports: () => <ReportsView />,
};

export function App() {
  return (
    <div className="app-stage">
      <AppShell renderView={(activeView) => views[activeView]()} />
    </div>
  );
}
