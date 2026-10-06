"""
Every column an ORM model selects must exist in the migrated database.

Regression: tasmee_* and theme_suggestions models referenced columns that no
migration created, so /api/v1/tasmee/progress and theme-suggestion queries
failed with 500 on a database built from `alembic upgrade head`.
"""
import importlib
import pkgutil

import pytest
from sqlalchemy import create_engine, inspect

from app.core.config import settings
from app.db.database import Base


def _load_all_models():
    import app.models as models
    for mod in pkgutil.iter_modules(models.__path__):
        importlib.import_module(f"app.models.{mod.name}")


def test_model_columns_exist_in_database():
    _load_all_models()
    try:
        engine = create_engine(settings.database_url)
        inspector = inspect(engine)
        db_tables = set(inspector.get_table_names())
    except Exception as exc:  # pragma: no cover - needs a database
        pytest.skip(f"database unavailable: {exc}")

    missing = []
    for table in Base.metadata.sorted_tables:
        if table.name not in db_tables:
            missing.append(f"{table.name} (table)")
            continue
        db_columns = {c["name"] for c in inspector.get_columns(table.name)}
        missing += [f"{table.name}.{c.name}" for c in table.columns if c.name not in db_columns]
    engine.dispose()
    assert not missing, f"Model columns missing from the migrated schema: {missing}"
