# TaskGame React RPG Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current manual TypeScript frontend with a centered React RPG/fantasy premium interface, while keeping the FastAPI/MySQL backend and Docker runtime working end to end.

**Architecture:** The backend API remains unchanged. The frontend becomes a React + TypeScript app built by Vite for development, with generated static assets committed in `frontend/dist` so Docker can serve the app without running npm inside the image. `liquidGL` is vendored as a browser script and initialized only on non-interactive decorative fixed elements with CSS fallback.

**Tech Stack:** React, TypeScript, Vite, CSS, FastAPI static file serving, Docker Compose, MySQL, vendored `naughtyduk/liquidGL`.

## Global Constraints

- Direction: **Guild Hall Premium**.
- Backend FastAPI, MySQL, Docker, rules of XP/gold/badges, and API endpoints remain unchanged.
- React + TypeScript replaces the manual TypeScript frontend.
- Build output remains served from `frontend/dist`.
- No login/register.
- No secrets in the frontend.
- `liquidGL` is decorative only: not on buttons, inputs, selects, textareas, mission lists, or cards with essential text.
- If `window.liquidGL` or WebGL fails, the app remains usable with CSS glass fallback.
- Layout must be usable at 360px width with no incoherent overlap.
- `prefers-reduced-motion` reduces decorative animation.
- Before completion, run full backend tests, frontend build, Docker Compose build/run, API smoke checks, MySQL write smoke, and visual responsive checks.

---

## File Structure

- Modify `frontend/index.html`: replace the old static shell with a Vite/React mount point and add the vendored `liquidGL` script.
- Create `frontend/package.json`: React/Vite scripts and dependencies.
- Create `frontend/tsconfig.json`: React TS compiler config.
- Create `frontend/vite.config.ts`: build from `frontend/index.html` into `frontend/dist`.
- Replace `frontend/src/*`: React app code organized by API, components, views, hooks, and utility formatters.
- Create `frontend/src/main.tsx`: React entrypoint.
- Create `frontend/src/App.tsx`: top-level app shell, navigation state, decorative background, and view routing.
- Create `frontend/src/api/client.ts`: typed fetch wrapper for existing API endpoints.
- Create `frontend/src/types.ts`: API response/request types matching backend schemas.
- Create `frontend/src/components/*`: reusable RPG UI pieces such as shell, hero, cards, buttons, forms, and liquid glass decorations.
- Create `frontend/src/views/*`: dashboard, missions, goals, badges, rewards, reports, backup views.
- Replace `frontend/styles/app.css`: RPG premium responsive design.
- Create `frontend/public/vendor/liquidGL.js`: vendored library file from `naughtyduk/liquidGL`.
- Modify `scripts/build_frontend.sh`: run `npm`/Vite when available; otherwise verify committed `frontend/dist` assets exist for Docker fallback.
- Modify `Dockerfile`: keep Docker independent from npm; copy generated frontend assets and scripts.
- Modify `backend/tests/test_frontend_static.py`: assert React/Vite shell, built assets, route/view coverage, liquidGL guardrails, and no old manual renderer assumptions.
- Modify `.gitignore`: allow committed production frontend assets needed by Docker fallback while still ignoring transient build caches.
- Modify `README.md`: document React/Vite development flow and Docker fallback behavior.

---

### Task 1: Frontend Tooling And Static Serving Contract

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Modify: `frontend/index.html`
- Modify: `scripts/build_frontend.sh`
- Modify: `Dockerfile`
- Modify: `.gitignore`
- Modify: `backend/tests/test_frontend_static.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `scripts/build_frontend.sh` behavior:
  - If `frontend/node_modules/.bin/vite` exists, run `npm --prefix frontend run build`.
  - Else if `npm` exists and `frontend/package-lock.json` exists, run `npm --prefix frontend ci` then build.
  - Else verify committed files exist under `frontend/dist`.
- Produces: Vite build output under `frontend/dist`.
- Consumes: FastAPI `StaticFiles(directory="frontend", html=True)` serving contract.

- [ ] **Step 1: Replace static frontend tests with failing React/Vite contract tests**

Edit `backend/tests/test_frontend_static.py` so the current assertions for manual modules are removed and these tests exist:

```python
from pathlib import Path
import re
import subprocess

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def test_frontend_index_is_react_shell_served_after_api_routes(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert '<div id="root"></div>' in response.text
    assert "/vendor/liquidGL.js" in response.text
    assert 'type="module"' in response.text


def test_frontend_has_vite_react_project_files():
    package_json = (FRONTEND / "package.json").read_text()
    vite_config = (FRONTEND / "vite.config.ts").read_text()
    tsconfig = (FRONTEND / "tsconfig.json").read_text()

    assert '"react"' in package_json
    assert '"@vitejs/plugin-react"' in package_json
    assert "outDir: \"dist\"" in vite_config
    assert '"jsx": "react-jsx"' in tsconfig


def test_react_app_routes_all_taskgame_views():
    app_source = (FRONTEND / "src" / "App.tsx").read_text()
    expected_views = [
        "DashboardView",
        "MissionsView",
        "GoalsView",
        "BadgesView",
        "RewardsView",
        "ReportsView",
        "BackupView",
    ]

    for view in expected_views:
        assert view in app_source


def test_liquidgl_is_decorative_and_guarded():
    liquid_source = (FRONTEND / "src" / "components" / "LiquidGlassDecor.tsx").read_text()

    assert "window.liquidGL" in liquid_source
    assert "try" in liquid_source
    assert "catch" in liquid_source
    assert "aria-hidden" in liquid_source
    assert "pointer-events-none" in liquid_source


def test_build_script_has_docker_safe_dist_fallback():
    source = (ROOT / "scripts" / "build_frontend.sh").read_text()

    assert "npm --prefix frontend run build" in source
    assert "frontend/dist" in source
    assert "React frontend build is missing" in source
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest backend/tests/test_frontend_static.py -v`

Expected: FAIL because `frontend/package.json`, `frontend/vite.config.ts`, React source files, and `LiquidGlassDecor.tsx` do not exist yet.

- [ ] **Step 3: Add Vite React project files**

Create `frontend/package.json`:

```json
{
  "name": "taskgame-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 127.0.0.1",
    "build": "vite build",
    "preview": "vite preview --host 127.0.0.1"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^5.0.0",
    "vite": "^7.0.0",
    "typescript": "^5.5.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {}
}
```

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2022"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
```

Create `frontend/vite.config.ts`:

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  root: ".",
  publicDir: "public",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
```

Replace `frontend/index.html` with:

```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>TaskGame</title>
  </head>
  <body>
    <div id="root"></div>
    <script src="/vendor/liquidGL.js" defer></script>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 4: Update build script with Docker-safe fallback**

Replace `scripts/build_frontend.sh` with:

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ -x "frontend/node_modules/.bin/vite" ]; then
  npm --prefix frontend run build
  exit 0
fi

if command -v npm >/dev/null 2>&1 && [ -f "frontend/package-lock.json" ]; then
  npm --prefix frontend ci
  npm --prefix frontend run build
  exit 0
fi

if [ -f "frontend/dist/index.html" ] && find frontend/dist/assets -type f -name '*.js' | grep -q .; then
  exit 0
fi

echo "React frontend build is missing. Run npm --prefix frontend ci && npm --prefix frontend run build." >&2
exit 127
```

- [ ] **Step 5: Keep Docker runtime npm-independent**

Keep `Dockerfile` on Python only. Ensure it still has:

```dockerfile
COPY frontend ./frontend
RUN scripts/build_frontend.sh
```

Do not add `npm install`, `apt-get`, or a Node build stage in this task.

- [ ] **Step 6: Add minimal React source stubs and liquid component file**

Create `frontend/src/main.tsx`:

```tsx
import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "../styles/app.css";

createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `frontend/src/App.tsx`:

```tsx
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
```

Create `frontend/src/components/LiquidGlassDecor.tsx`:

```tsx
import { useEffect } from "react";

declare global {
  interface Window {
    liquidGL?: (options: Record<string, unknown>) => unknown;
  }
}

export function LiquidGlassDecor() {
  useEffect(() => {
    try {
      window.liquidGL?.({
        target: ".liquid-glass-decor",
        snapshot: "body",
        refraction: 0.018,
        frost: 0.18,
        tilt: false,
      });
    } catch {
      document.documentElement.classList.add("liquidgl-unavailable");
    }
  }, []);

  return <div className="liquid-glass-decor pointer-events-none" aria-hidden="true" />;
}
```

Create view stubs exporting each view name with `hidden?: boolean`.

- [ ] **Step 7: Update ignores for Vite caches while allowing committed dist**

Edit `.gitignore` so it ignores:

```gitignore
frontend/node_modules/
frontend/.vite/
```

Remove ignore rules that prevent committing `frontend/dist` production assets.

- [ ] **Step 8: Install dependencies and generate package lock**

Run: `npm --prefix frontend install`

Expected: `frontend/package-lock.json` exists.

- [ ] **Step 9: Build frontend and run focused tests**

Run: `scripts/build_frontend.sh`

Expected: Vite builds into `frontend/dist`.

Run: `.venv/bin/pytest backend/tests/test_frontend_static.py -v`

Expected: PASS.

- [ ] **Step 10: Commit tooling contract**

```bash
git add .gitignore Dockerfile README.md backend/tests/test_frontend_static.py frontend scripts/build_frontend.sh
git commit -m "feat: add react frontend build contract"
```

---

### Task 2: React API Client And Shared View State

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/hooks/useAsyncData.ts`
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/components/AppShell.tsx`
- Create: `frontend/src/components/StatePanels.tsx`

**Interfaces:**
- Produces: `apiGet<T>(path: string): Promise<T>`
- Produces: `apiPost<TResponse, TBody = unknown>(path: string, body?: TBody): Promise<TResponse>`
- Produces: `apiPatch<TResponse, TBody = unknown>(path: string, body: TBody): Promise<TResponse>`
- Produces: `useAsyncData<T>(loader: () => Promise<T>, deps: React.DependencyList): AsyncData<T>`
- Produces: `AppShell` with view navigation state and centered RPG layout.

- [ ] **Step 1: Write failing source contract tests**

Add to `backend/tests/test_frontend_static.py`:

```python
def test_react_api_client_wraps_existing_backend_endpoints():
    source = (FRONTEND / "src" / "api" / "client.ts").read_text()

    assert "export async function apiGet" in source
    assert "export async function apiPost" in source
    assert "export async function apiPatch" in source
    assert 'fetch(`/api${path}`' in source
    assert "throw new Error" in source


def test_react_app_uses_stateful_shell_navigation():
    source = (FRONTEND / "src" / "components" / "AppShell.tsx").read_text()

    for view in ("dashboard", "missions", "goals", "badges", "rewards", "reports", "backup"):
        assert view in source
    assert "useState<ViewKey>" in source
    assert "setActiveView" in source
```

- [ ] **Step 2: Run tests to verify failure**

Run: `.venv/bin/pytest backend/tests/test_frontend_static.py::test_react_api_client_wraps_existing_backend_endpoints backend/tests/test_frontend_static.py::test_react_app_uses_stateful_shell_navigation -v`

Expected: FAIL because files/functions do not exist or are still stubs.

- [ ] **Step 3: Create TypeScript API types**

Create `frontend/src/types.ts` containing enums/unions and interfaces for:

```ts
export type ViewKey = "dashboard" | "missions" | "goals" | "badges" | "rewards" | "reports" | "backup";
export type MissionType = "daily" | "weekly" | "long_term";
export type Difficulty = "easy" | "medium" | "hard" | "epic";
export type MissionStatus = "active" | "completed" | "archived";

export interface PlayerSummary {
  total_xp: number;
  gold: number;
  level: number;
  xp_into_level: number;
  xp_for_next_level: number;
  current_streak: number;
  best_streak: number;
}
```

Also define `Mission`, `MissionCreatePayload`, `MissionProgressPayload`, `MissionCompletion`, `BadgeStatus`, `Reward`, `RewardCreatePayload`, `RewardPurchase`, `WeeklyReport`, `BackupStatus`, and `DashboardData` matching `backend/app/schemas.py`.

- [ ] **Step 4: Create fetch client**

Create `frontend/src/api/client.ts`:

```ts
async function request<TResponse>(path: string, init?: RequestInit): Promise<TResponse> {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return (await response.json()) as TResponse;
}

export async function apiGet<TResponse>(path: string): Promise<TResponse> {
  return request<TResponse>(path);
}

export async function apiPost<TResponse, TBody = unknown>(path: string, body?: TBody): Promise<TResponse> {
  return request<TResponse>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export async function apiPatch<TResponse, TBody = unknown>(path: string, body: TBody): Promise<TResponse> {
  return request<TResponse>(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}
```

- [ ] **Step 5: Create async data hook**

Create `frontend/src/hooks/useAsyncData.ts` with:

```ts
import { useEffect, useState } from "react";

export type AsyncData<T> =
  | { status: "loading"; data: null; error: null }
  | { status: "ready"; data: T; error: null }
  | { status: "error"; data: null; error: string };

export function useAsyncData<T>(loader: () => Promise<T>, deps: React.DependencyList): AsyncData<T> {
  const [state, setState] = useState<AsyncData<T>>({ status: "loading", data: null, error: null });

  useEffect(() => {
    let active = true;
    setState({ status: "loading", data: null, error: null });
    loader()
      .then((data) => {
        if (active) setState({ status: "ready", data, error: null });
      })
      .catch((error: unknown) => {
        if (active) setState({ status: "error", data: null, error: error instanceof Error ? error.message : "Erro inesperado" });
      });
    return () => {
      active = false;
    };
  }, deps);

  return state;
}
```

- [ ] **Step 6: Create shell/navigation**

Create `frontend/src/components/AppShell.tsx` with view buttons and `useState<ViewKey>("dashboard")`. It renders one current view function passed by props. Use labels:

```ts
const navigation = [
  { key: "dashboard", label: "Salao", eyebrow: "Personagem" },
  { key: "missions", label: "Missoes", eyebrow: "Contratos" },
  { key: "goals", label: "Campanhas", eyebrow: "Objetivos" },
  { key: "badges", label: "Medalhas", eyebrow: "Conquistas" },
  { key: "rewards", label: "Loja", eyebrow: "Ouro" },
  { key: "reports", label: "Cronica", eyebrow: "Semana" },
  { key: "backup", label: "Arquivo", eyebrow: "Dados" },
] as const;
```

- [ ] **Step 7: Wire App through shell**

Modify `frontend/src/App.tsx` to render `AppShell` and switch views by `activeView`.

- [ ] **Step 8: Build and test**

Run: `scripts/build_frontend.sh`

Run: `.venv/bin/pytest backend/tests/test_frontend_static.py -v`

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add backend/tests/test_frontend_static.py frontend/src frontend/dist
git commit -m "feat: add react app shell and api client"
```

---

### Task 3: Guild Hall Dashboard And Premium Styling Foundation

**Files:**
- Create: `frontend/src/views/DashboardView.tsx`
- Create: `frontend/src/components/ProgressBar.tsx`
- Create: `frontend/src/components/MetricCard.tsx`
- Create: `frontend/src/components/MissionCard.tsx`
- Create: `frontend/src/components/LiquidGlassDecor.tsx`
- Modify: `frontend/styles/app.css`
- Modify: `backend/tests/test_frontend_static.py`

**Interfaces:**
- Consumes: `apiGet<DashboardData>("/dashboard")`
- Produces: centered shell classes: `app-stage`, `guild-shell`, `guild-main`, `hero-panel`, `quest-card`, `liquid-glass-decor`
- Produces: `ProgressBar({ value, max, label })`

- [ ] **Step 1: Add failing CSS/design guardrail tests**

Add to `backend/tests/test_frontend_static.py`:

```python
def test_rpg_theme_css_contains_centered_premium_tokens():
    css = (FRONTEND / "styles" / "app.css").read_text()

    assert "--color-void" in css
    assert "--color-arcane" in css
    assert "--color-gold" in css
    assert "max-width: 1440px" in css
    assert ".hero-panel" in css
    assert ".quest-card" in css
    assert "@media (max-width: 720px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_dashboard_view_uses_live_dashboard_endpoint():
    source = (FRONTEND / "src" / "views" / "DashboardView.tsx").read_text()

    assert 'apiGet<DashboardData>("/dashboard")' in source
    assert "XP para o proximo nivel" in source
    assert "Missoes de hoje" in source
    assert "Ouro" in source
```

- [ ] **Step 2: Run failing tests**

Run: `.venv/bin/pytest backend/tests/test_frontend_static.py::test_rpg_theme_css_contains_centered_premium_tokens backend/tests/test_frontend_static.py::test_dashboard_view_uses_live_dashboard_endpoint -v`

Expected: FAIL until CSS and dashboard are implemented.

- [ ] **Step 3: Implement dashboard data rendering**

Create `DashboardView.tsx` that loads `DashboardData`, displays loading/error states, and renders:

- Level hero.
- XP progress.
- Gold.
- Current/best streak.
- Today completed/active/overdue.
- Weekly completed/XP/gold/best day.
- Upcoming missions using `MissionCard`.
- Recent badge block.

- [ ] **Step 4: Implement reusable cards**

Create `ProgressBar.tsx`, `MetricCard.tsx`, and `MissionCard.tsx` with typed props and no direct API calls.

- [ ] **Step 5: Replace CSS with premium responsive theme**

Replace `frontend/styles/app.css` with a centered RPG visual foundation using:

- `--color-void: #03050b`
- `--color-night: #080d18`
- `--color-panel: #111827`
- `--color-arcane: #1d8cff`
- `--color-gold: #d7a928`
- `max-width: 1440px`
- mobile media query at `720px`
- reduced motion media query
- decorative background without bokeh/orbs

- [ ] **Step 6: Build and test**

Run: `scripts/build_frontend.sh`

Run: `.venv/bin/pytest backend/tests/test_frontend_static.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/tests/test_frontend_static.py frontend/src frontend/styles frontend/dist
git commit -m "feat: redesign dashboard as guild hall"
```

---

### Task 4: React Mission, Goal, Badge, Reward, Report, And Backup Views

**Files:**
- Create/Modify: `frontend/src/views/MissionsView.tsx`
- Create/Modify: `frontend/src/views/GoalsView.tsx`
- Create/Modify: `frontend/src/views/BadgesView.tsx`
- Create/Modify: `frontend/src/views/RewardsView.tsx`
- Create/Modify: `frontend/src/views/ReportsView.tsx`
- Create/Modify: `frontend/src/views/BackupView.tsx`
- Create: `frontend/src/components/FormControls.tsx`
- Create: `frontend/src/components/BadgeTile.tsx`
- Create: `frontend/src/components/RewardCard.tsx`
- Modify: `frontend/styles/app.css`
- Modify: `backend/tests/test_frontend_static.py`

**Interfaces:**
- Consumes existing API endpoints:
  - `GET /api/missions?include_archived=true`
  - `POST /api/missions`
  - `PATCH /api/missions/{id}`
  - `POST /api/missions/{id}/complete`
  - `POST /api/missions/{id}/archive`
  - `POST /api/missions/{id}/progress`
  - `GET /api/goals`
  - `GET /api/badges`
  - `GET /api/rewards`
  - `POST /api/rewards`
  - `POST /api/rewards/{id}/purchase`
  - `GET /api/rewards/purchases`
  - `GET /api/reports/weekly`
  - `GET /api/backup/status`
- Produces usable React views for every navigation item.

- [ ] **Step 1: Add failing source coverage tests**

Add to `backend/tests/test_frontend_static.py`:

```python
def test_missions_view_supports_create_complete_progress_and_archive_flows():
    source = (FRONTEND / "src" / "views" / "MissionsView.tsx").read_text()

    assert 'apiGet<Mission[]>("/missions?include_archived=true")' in source
    assert 'apiPost<Mission, MissionCreatePayload>("/missions"' in source
    assert '`/missions/${mission.id}/complete`' in source
    assert '`/missions/${mission.id}/archive`' in source
    assert '`/missions/${mission.id}/progress`' in source


def test_rewards_reports_backup_views_use_existing_endpoints():
    rewards = (FRONTEND / "src" / "views" / "RewardsView.tsx").read_text()
    reports = (FRONTEND / "src" / "views" / "ReportsView.tsx").read_text()
    backup = (FRONTEND / "src" / "views" / "BackupView.tsx").read_text()

    assert 'apiGet<Reward[]>("/rewards")' in rewards
    assert 'apiPost<Reward, RewardCreatePayload>("/rewards"' in rewards
    assert 'apiPost<RewardPurchase>(`/rewards/${reward.id}/purchase`)' in rewards
    assert 'apiGet<WeeklyReport>("/reports/weekly")' in reports
    assert 'apiGet<BackupStatus>("/backup/status")' in backup
    assert 'href="/api/backup/export.json"' in backup
    assert 'href="/api/backup/missions.csv"' in backup
    assert 'href="/api/backup/completions.csv"' in backup
```

- [ ] **Step 2: Run failing tests**

Run: `.venv/bin/pytest backend/tests/test_frontend_static.py::test_missions_view_supports_create_complete_progress_and_archive_flows backend/tests/test_frontend_static.py::test_rewards_reports_backup_views_use_existing_endpoints -v`

Expected: FAIL until the views use the required endpoints.

- [ ] **Step 3: Implement mission and goals views**

Implement mission create form with fields:

- `title`
- `description`
- `type`
- `difficulty`
- `category`
- `target_date`
- `progress_target`

Render existing missions as `MissionCard` and provide buttons for complete, archive, and progress where relevant.

- [ ] **Step 4: Implement badges and rewards views**

Render medals as RPG tiles and rewards as shop item cards. Reward creation requires `name` and `cost`; purchase calls the existing endpoint and refreshes data.

- [ ] **Step 5: Implement reports and backup views**

Reports render weekly numeric cards and daily bars. Backup renders export links and latest MySQL dump status.

- [ ] **Step 6: Build and test**

Run: `scripts/build_frontend.sh`

Run: `.venv/bin/pytest backend/tests/test_frontend_static.py backend/tests/test_missions_api.py backend/tests/test_rewards_api.py backend/tests/test_reports_dashboard.py backend/tests/test_backup_exports.py -v`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/tests/test_frontend_static.py frontend/src frontend/styles frontend/dist
git commit -m "feat: add react quest management views"
```

---

### Task 5: liquidGL Vendor Integration And Visual Verification

**Files:**
- Create: `frontend/public/vendor/liquidGL.js`
- Modify: `frontend/src/components/LiquidGlassDecor.tsx`
- Modify: `frontend/styles/app.css`
- Modify: `backend/tests/test_frontend_static.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: browser global `window.liquidGL`.
- Produces: decorative fixed `.liquid-glass-decor` elements with CSS fallback and no pointer events.

- [ ] **Step 1: Add failing vendor/guardrail tests**

Add to `backend/tests/test_frontend_static.py`:

```python
def test_liquidgl_vendor_file_exists_and_is_loaded_before_app():
    index = (FRONTEND / "index.html").read_text()
    vendor = FRONTEND / "public" / "vendor" / "liquidGL.js"

    assert vendor.exists()
    assert vendor.stat().st_size > 1000
    assert '<script src="/vendor/liquidGL.js" defer></script>' in index


def test_liquidgl_css_never_targets_interactive_controls():
    css = (FRONTEND / "styles" / "app.css").read_text()

    forbidden = [
        ".button.liquid",
        "input.liquid",
        "select.liquid",
        "textarea.liquid",
        ".quest-card.liquid-glass-decor",
    ]
    for selector in forbidden:
        assert selector not in css
```

- [ ] **Step 2: Run failing tests**

Run: `.venv/bin/pytest backend/tests/test_frontend_static.py::test_liquidgl_vendor_file_exists_and_is_loaded_before_app backend/tests/test_frontend_static.py::test_liquidgl_css_never_targets_interactive_controls -v`

Expected: FAIL until the vendor file exists.

- [ ] **Step 3: Vendor liquidGL**

Download the current `naughtyduk/liquidGL` browser script into `frontend/public/vendor/liquidGL.js`. Preserve any license/header comments present in the source. If the repository exposes a license file, note it in `README.md`.

- [ ] **Step 4: Finalize decorative initialization**

Ensure `LiquidGlassDecor.tsx` initializes only `.liquid-glass-decor`, catches failures, uses `aria-hidden="true"`, and gives every decorative element `pointer-events-none`.

- [ ] **Step 5: Build and test**

Run: `scripts/build_frontend.sh`

Run: `.venv/bin/pytest backend/tests/test_frontend_static.py -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add README.md backend/tests/test_frontend_static.py frontend/public frontend/src/components/LiquidGlassDecor.tsx frontend/styles frontend/dist
git commit -m "feat: add decorative liquid glass effects"
```

---

### Task 6: End-To-End Docker Runtime Verification

**Files:**
- Modify: `README.md`
- No frontend source changes unless verification exposes a concrete bug.

**Interfaces:**
- Consumes: complete React static build in `frontend/dist`.
- Produces: verified Docker runtime at `http://127.0.0.1:8000`.

- [ ] **Step 1: Run full local verification**

Run:

```bash
scripts/build_frontend.sh
.venv/bin/pytest backend/tests -v
git diff --check
```

Expected:

- Frontend build exits 0.
- All backend tests pass.
- `git diff --check` exits 0.

- [ ] **Step 2: Rebuild and start Docker Compose**

Run:

```bash
docker compose --env-file .env.example up -d --build
```

Expected: app and db containers start; db is healthy; app is published at `127.0.0.1:8000`.

- [ ] **Step 3: Smoke API and frontend assets**

Run:

```bash
curl -fsS http://127.0.0.1:8000/api/health
curl -fsSI http://127.0.0.1:8000/
curl -fsS http://127.0.0.1:8000/api/dashboard
```

Expected:

- Health returns `{"status":"ok","app":"TaskGame"}`.
- `/` returns HTTP 200.
- Dashboard returns JSON with `player`, `today`, and `weekly`.

- [ ] **Step 4: Smoke MySQL write through API**

Run:

```bash
MISSION_JSON=$(curl -fsS -X POST http://127.0.0.1:8000/api/missions -H 'Content-Type: application/json' --data '{"title":"Smoke React Docker API","type":"daily","difficulty":"easy","category":"smoke"}')
MISSION_ID=$(printf '%s' "$MISSION_JSON" | .venv/bin/python -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -fsS -X POST "http://127.0.0.1:8000/api/missions/$MISSION_ID/complete"
curl -fsS http://127.0.0.1:8000/api/dashboard
```

Expected: completion returns XP/gold and dashboard reflects the completed mission.

- [ ] **Step 5: Smoke backup script in container**

Run:

```bash
docker compose --env-file .env.example exec -T app scripts/backup_mysql.sh
```

Expected: prints `/app/backups/mysql/taskgame-<timestamp>.sql.gz`.

- [ ] **Step 6: Visual responsive verification**

Use a browser or Playwright to inspect:

- Desktop width around `1440x900`.
- Mobile width around `390x844`.
- Confirm the app is not blank.
- Confirm the main content is centered.
- Confirm RPG premium design is visible.
- Confirm no overlapping text/buttons.
- Confirm `liquidGL` decorations do not block clicks.

- [ ] **Step 7: Clean smoke data created by this task**

Run:

```bash
docker compose --env-file .env.example exec -T -e MYSQL_PWD=change-me db mysql -utaskgame taskgame -e "DELETE mc FROM mission_completions mc JOIN missions m ON m.id = mc.mission_id WHERE m.title = 'Smoke React Docker API'; DELETE FROM missions WHERE title = 'Smoke React Docker API'; UPDATE player_stats SET total_xp = 0, gold = 0, current_streak = 0, best_streak = 0, last_active_date = NULL WHERE id = 1;"
```

Expected: dashboard returns to the pre-smoke state.

- [ ] **Step 8: Commit final docs or fixes**

If only README changed:

```bash
git add README.md
git commit -m "docs: document react frontend workflow"
```

If verification required source fixes, commit them with a `fix:` message describing the concrete issue.

---

## Self-Review

- Spec coverage: React migration is covered by Tasks 1-2; Guild Hall Premium and centered responsive layout by Task 3; all required screens by Task 4; decorative `liquidGL` usage and fallback by Task 5; Docker/runtime/backup/API smoke checks by Task 6.
- Placeholder scan: no unfinished marker words or unspecified "handle later" requirements remain.
- Type consistency: `ViewKey`, API client method names, view component names, and endpoint strings are defined before later tasks consume them.
