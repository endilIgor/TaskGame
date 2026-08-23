import { useEffect, useState } from "react";
import { apiGetOptional } from "./api/client";
import { DashboardView } from "./views/DashboardView";
import { MissionsView } from "./views/MissionsView";
import { JournalView } from "./views/JournalView";
import { GoalsView } from "./views/GoalsView";
import { BadgesView } from "./views/BadgesView";
import { RewardsView } from "./views/RewardsView";
import { ReportsView } from "./views/ReportsView";
import { OnboardingView } from "./views/OnboardingView";
import { AppShell } from "./components/AppShell";
import { ErrorPanel, LoadingPanel } from "./components/StatePanels";
import type { ReactNode } from "react";
import type { PlayerProfile, ViewKey } from "./types";

const views: Record<ViewKey, () => ReactNode> = {
  dashboard: () => <DashboardView />,
  missions: () => <MissionsView />,
  journal: () => <JournalView />,
  goals: () => <GoalsView />,
  badges: () => <BadgesView />,
  rewards: () => <RewardsView />,
  reports: () => <ReportsView />,
};

type AppStatus = "loading" | "onboarding" | "ready" | "error";

export function App() {
  const [status, setStatus] = useState<AppStatus>("loading");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    apiGetOptional<PlayerProfile>("/profile")
      .then((profile) => {
        if (!active) return;
        setStatus(profile ? "ready" : "onboarding");
      })
      .catch((cause: unknown) => {
        if (!active) return;
        setError(cause instanceof Error ? cause.message : "Erro inesperado");
        setStatus("error");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="app-stage">
      {status === "loading" ? <LoadingPanel /> : null}
      {status === "error" ? <ErrorPanel>{error}</ErrorPanel> : null}
      {status === "onboarding" ? <OnboardingView onComplete={() => setStatus("ready")} /> : null}
      {status === "ready" ? <AppShell renderView={(activeView) => views[activeView]()} /> : null}
    </div>
  );
}
