"""Production configuration guards (no secrets are ever printed)."""
from pydantic import SecretStr

from app.core.config import Settings
from app.core.production_checks import production_config_problems, safe_cors_origins


def test_wildcard_cors_is_dropped_in_production_only():
    assert safe_cors_origins(["*", "https://app.example"], "production") == ["https://app.example"]
    assert safe_cors_origins(["*"], "development") == ["*"]


def test_production_problems_are_reported():
    s = Settings(_env_file=None, environment="production", hf_token=None, admin_api_key=None,
                 database_url="postgresql://u:p@localhost:5432/db")
    problems = " | ".join(production_config_problems(s, ["http://api.example"], cors_env_set=False))
    for needle in ("HF_TOKEN", "ADMIN_API_KEY", "CORS_ORIGINS is not set", "non-HTTPS", "DATABASE_URL"):
        assert needle in problems


def test_clean_production_config_has_no_problems():
    s = Settings(_env_file=None, environment="production", hf_token=SecretStr("hf_x"),
                 admin_api_key="k" * 32, database_url="postgresql://u:p@db:5432/db",
                 qdrant_host="qdrant", redis_url="redis://redis:6379/0")
    origins = ["https://app.example", "capacitor://localhost", "https://localhost"]
    assert production_config_problems(s, origins, cors_env_set=True) == []
    assert s.debug is False


def test_problems_never_contain_secret_values():
    s = Settings(_env_file=None, environment="production", hf_token=SecretStr("hf_secret_should_not_print"),
                 admin_api_key="admin_secret_value", database_url="postgresql://u:pw@localhost/db")
    text = " ".join(production_config_problems(s, [], cors_env_set=False))
    assert "hf_secret_should_not_print" not in text and "admin_secret_value" not in text and "pw" not in text
