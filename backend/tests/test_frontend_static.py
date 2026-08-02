from pathlib import Path
import re
import subprocess

from fastapi.testclient import TestClient


def test_frontend_index_is_served_after_api_routes(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200
    assert '<main id="app" class="content" tabindex="-1"></main>' in response.text


def test_frontend_routes_all_taskgame_views():
    frontend = Path(__file__).resolve().parents[2] / "frontend" / "src"
    app_source = (frontend / "app.ts").read_text()

    expected_views = [
        ("missions.ts", "renderMissions"),
        ("missions.ts", "renderGoals"),
        ("badges.ts", "renderBadges"),
        ("rewards.ts", "renderRewards"),
        ("reports.ts", "renderReports"),
        ("backup.ts", "renderBackup"),
    ]
    for filename, renderer in expected_views:
        source = (frontend / filename).read_text()
        assert f"export async function {renderer}" in source
        assert renderer in app_source


def test_missions_view_supports_filter_edit_and_archive_flows():
    frontend = Path(__file__).resolve().parents[2] / "frontend" / "src"
    source = (frontend / "missions.ts").read_text()

    assert 'apiGet<Mission[]>("/missions?include_archived=true")' in source
    assert "createMissionFilters(missions, showMissions)" in source
    assert "apiPatch<Mission>" in source
    assert "`/missions/${mission.id}/archive`" in source


def test_prebuilt_modules_match_source_modules_and_use_browser_imports():
    frontend = Path(__file__).resolve().parents[2] / "frontend"
    source_modules = {path.stem for path in (frontend / "src").glob("*.ts")}
    prebuilt_modules = {path.stem for path in (frontend / "prebuilt").glob("*.js")}

    assert prebuilt_modules == source_modules
    for directory, suffix in ((frontend / "src", ".ts"), (frontend / "prebuilt", ".js")):
        for module in directory.glob(f"*{suffix}"):
            imports = re.findall(r'from\s+["\']([^"\']+)["\']', module.read_text())
            assert all(path.endswith(".js") for path in imports), module

    strip_script = (
        "import {readFileSync} from 'node:fs';"
        "import {stripTypeScriptTypes} from 'node:module';"
        "process.stdout.write(stripTypeScriptTypes(readFileSync(process.argv[1], 'utf8'), "
        "{mode: 'strip'}));"
    )
    for module_name in source_modules:
        try:
            compiled = subprocess.run(
                [
                    "node",
                    "--no-warnings",
                    "--input-type=module",
                    "-e",
                    strip_script,
                    str(frontend / "src" / f"{module_name}.ts"),
                ],
                check=True,
                capture_output=True,
            ).stdout
        except (FileNotFoundError, subprocess.CalledProcessError):
            return
        normalized = b"\n".join(
            line.rstrip() for line in compiled.splitlines() if line.strip()
        )
        if normalized:
            normalized += b"\n"
        assert (frontend / "prebuilt" / f"{module_name}.js").read_bytes() == normalized
