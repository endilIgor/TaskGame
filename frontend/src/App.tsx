import { LiquidGlassDecor } from "./components/LiquidGlassDecor";
import { DashboardView } from "./views/DashboardView";
import { MissionsView } from "./views/MissionsView";
import { GoalsView } from "./views/GoalsView";
import { BadgesView } from "./views/BadgesView";
import { RewardsView } from "./views/RewardsView";
import { ReportsView } from "./views/ReportsView";
import { BackupView } from "./views/BackupView";
import { AppShell } from "./components/AppShell";
import type { ReactNode } from "react";
import type { ViewKey } from "./types";

const views: Record<ViewKey, () => ReactNode> = {
  dashboard: () => <DashboardView />,
  missions: () => <MissionsView />,
  goals: () => <GoalsView />,
  badges: () => <BadgesView />,
  rewards: () => <RewardsView />,
  reports: () => <ReportsView />,
  backup: () => <BackupView />,
};

export function App() {
  return (
    <div className="app-stage">
      <LiquidGlassDecor />
      <AppShell renderView={(activeView) => views[activeView]()} />
    </div>
  );
}
