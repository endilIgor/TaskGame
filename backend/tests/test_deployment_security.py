from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_docker_context_excludes_local_env_but_retains_example():
    patterns = (ROOT / ".dockerignore").read_text().splitlines()

    assert ".env" in patterns
    assert ".env.*" in patterns
    assert "!.env.example" in patterns


def test_compose_binds_app_to_loopback_by_default():
    compose = (ROOT / "docker-compose.yml").read_text()

    assert "${APP_BIND_ADDRESS:-127.0.0.1}" in compose


def test_database_scripts_use_injected_environment_without_password_arguments():
    for name in ("backup_mysql.sh", "restore_mysql.sh"):
        source = (ROOT / "scripts" / name).read_text()
        assert ". ./.env" not in source
        assert '--password="$MYSQL_PASSWORD"' not in source
        assert "python -m backend.app.services.mysql_dump" in source


def test_dockerfile_does_not_require_apt_packages_for_runtime():
    source = (ROOT / "Dockerfile").read_text()

    assert "apt-get" not in source
    assert "default-mysql-client" not in source
    assert "node-typescript" not in source


def test_dockerfile_installs_python_dependencies_from_local_wheelhouse():
    source = (ROOT / "Dockerfile").read_text()

    assert "COPY vendor/wheels /wheels" in source
    assert "--no-index" in source
    assert "--find-links=/wheels" in source


def test_dockerfile_uses_explicit_project_copies():
    source = (ROOT / "Dockerfile").read_text()

    assert "COPY . ." not in source
    assert "COPY backend ./backend" in source
    assert "COPY frontend ./frontend" in source
    assert "COPY scripts ./scripts" in source
