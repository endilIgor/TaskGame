import { LiquidGlassDecor } from "./components/LiquidGlassDecor";
import { DashboardView } from "./views/DashboardView";
import { MissionsView } from "./views/MissionsView";
import { GoalsView } from "./views/GoalsView";
import { BadgesView } from "./views/BadgesView";
import { RewardsView } from "./views/RewardsView";
import { ReportsView } from "./views/ReportsView";
import { BackupView } from "./views/BackupView";

export function App() {
  return (
    <div className="app-stage">
      <LiquidGlassDecor />
      <DashboardView />
      <MissionsView hidden />
      <GoalsView hidden />
      <BadgesView hidden />
      <RewardsView hidden />
      <ReportsView hidden />
      <BackupView hidden />
    </div>
  );
}
