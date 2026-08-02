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
        assert "--defaults-extra-file" in source
