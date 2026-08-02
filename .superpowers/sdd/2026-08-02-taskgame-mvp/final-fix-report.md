# TaskGame MVP Final Fix Report

Date: 2026-08-02
Base HEAD: `30c893e`
Fix commit: `fix: resolve final MVP review blockers` (this commit)

## Findings Addressed

1. Docker build secret exposure: added `.env` and `.env.*` to `.dockerignore`, retained `.env.example` with a negation rule, and removed implicit `.env` sourcing from both MySQL scripts. Container scripts now use only injected environment variables.

2. Mission completion eligibility: removed the public `completed_on` query parameter. Completion now rejects non-active missions, future dates, missions before `start_date`, off-schedule daily missions, and unfinished long-term missions. Empty daily recurrence remains every day. Weekly completion keys are ISO-week scoped.

3. Long-term threshold rewards: progress updates now lock the mission and route a target-reaching transition through the same transaction-owned completion function used by direct completion. The transition creates a completion, awards XP/gold, changes status, evaluates badges, and commits atomically.

4. Daily-routine streaks: moved streak derivation into `backend/app/services/streaks.py`. Only scheduled daily completion history contributes. Prior scheduled days require all active daily obligations, unscheduled days are neutral, weekly/long-term rewards do not advance streak, out-of-order historical completions are recalculated safely, and dashboard/report reads clear stale streaks after inactivity.

5. Unauthenticated LAN exposure: Compose now publishes the app on `127.0.0.1` by default through `APP_BIND_ADDRESS`. README documents explicit LAN opt-in and the authentication risk.

6. CSV formula injection: formula detection now skips leading whitespace and Unicode control/format characters before checking `=`, `+`, `-`, or `@`. All exported cells still pass through the sanitizer. Tests cover tabs, CR/LF, spaces, ASCII controls, BOM, and zero-width space bypasses.

7. MVP UI coverage: missions now expose description/dates/progress fields, edit, type/status/text filters, and archive. Rewards now expose edit, archive, archived items, and purchase history. Reports now expose week selection, real daily bars, top categories, and completed-goal analysis. Backup now shows latest MySQL dump metadata from a constrained backend status endpoint. Unsupported goal progress-event wording was narrowed in the design spec.

8. `APP_HOST` and `APP_PORT`: the Docker Uvicorn command now reads both settings, and Compose uses `APP_PORT` for host/container mapping. `APP_BIND_ADDRESS` separately controls host publication.

9. MySQL dump hardening: backup/restore use `umask 077` and temporary mode-protected client option files instead of password arguments. Backup writes to a protected temporary file, cleans up on exit, rejects final-name collisions, and atomically renames on success.

10. Frontend fallback integrity: tests verify source/prebuilt module sets and browser `.js` imports. On Node versions with native type stripping, tests deterministically compile every TypeScript module, normalize generated whitespace, and compare it byte-for-byte with the checked-in prebuilt module. All fallback modules were regenerated and parsed by Node.

## Files Changed

- Deployment and docs: `.dockerignore`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `README.md`, `docs/superpowers/specs/2026-08-02-taskgame-design.md`.
- Scripts: `scripts/backup_mysql.sh`, `scripts/restore_mysql.sh`.
- Backend routes/schemas: `backend/app/routers/backup.py`, `backend/app/routers/missions.py`, `backend/app/routers/rewards.py`, `backend/app/schemas.py`.
- Backend services: `backend/app/services/backup.py`, `backend/app/services/missions.py`, `backend/app/services/reports.py`, `backend/app/services/rewards.py`, `backend/app/services/streaks.py`.
- Frontend source: `frontend/src/api.ts`, `frontend/src/backup.ts`, `frontend/src/missions.ts`, `frontend/src/reports.ts`, `frontend/src/rewards.ts`, `frontend/src/types.ts`, `frontend/styles/app.css`.
- Frontend fallback: all nine modules under `frontend/prebuilt/`.
- Tests: `backend/tests/test_backup_exports.py`, `backend/tests/test_deployment_security.py`, `backend/tests/test_frontend_static.py`, `backend/tests/test_mission_streaks.py`, `backend/tests/test_missions_api.py`, `backend/tests/test_reports_dashboard.py`, `backend/tests/test_rewards_api.py`.

## Verification

- `scripts/build_frontend.sh`: exit 0, no output. The local environment had no `tsc`, so the checked-in fallback path was exercised.
- `node --check frontend/dist/*.js`: exit 0, no output.
- `.venv/bin/pytest backend/tests -v`: exit 0; `53 passed, 1 warning in 1.50s`. The warning is the existing Starlette/httpx deprecation warning.
- `docker compose --env-file .env.example config`: exit 0; rendered app port has `host_ip: 127.0.0.1`, target/published port `8000`.
- `bash -n scripts/backup_mysql.sh scripts/restore_mysql.sh`: exit 0, no output.
- `git diff --check`: exit 0, no output.
- `git status --short`: expected fix-wave changes only before commit.
- Live Uvicorn smoke test on `127.0.0.1:8001`: `/api/health`, `/`, `/dist/app.js`, and `/api/backup/status` all returned HTTP 200; server shut down cleanly.
- `docker compose --env-file .env.example build`: failed at Dockerfile package installation with exit 100. Exact root error: `Temporary failure resolving 'deb.debian.org'`; apt then reported it could not locate `default-mysql-client` and `node-typescript`.

## Remaining Concerns

- A full Docker image build could not be completed until this environment can resolve `deb.debian.org`. Compose configuration itself validates.
- Browser automation was unavailable because `agent-browser` is not installed (`command not found`). Live HTTP/static-module smoke checks passed, but no automated visual screenshot was produced.
- Historical streak reconstruction uses missions that are currently active because the MVP schema does not store an archive-effective timestamp. New completions and current dashboard/report state follow the required active daily-routine policy.

## Commit

Created commit: `fix: resolve final MVP review blockers`.
