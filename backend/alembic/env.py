"""
Alembic environment configuration for database migrations.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.base import Base
from app.db.models import (  # noqa: F401
    AssetModel,
    FinancialProfileModel,
    HistoricalPriceModel,
    InvestmentGoalModel,
    OptimizationRunModel,
    PortfolioHoldingModel,
    PortfolioModel,
    TargetAllocationModel,
    TransactionModel,
    UserModel,
    UserSessionModel,
)
from app.db.session import get_database_url

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """Return the database URL from environment or alembic config."""
    env_url = get_database_url()
    if env_url:
        return env_url
    return config.get_main_option("sqlalchemy.url", "sqlite:///./data/financial_portfolio.db")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    ini_section = config.get_section(config.config_ini_section, {})
    ini_section["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        ini_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
