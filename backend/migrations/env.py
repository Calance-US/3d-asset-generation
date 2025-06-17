from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from app.database.db_config import Base  # Import Base from db_config
from app.models import Prompt, Tag  # Import all models here
from app.config.settings import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Use the database URL directly from settings
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = settings.DATABASE_URL

    # Detect if using SQLite
    is_sqlite = url.startswith("sqlite")

    # Build configuration dict accordingly
    configuration = {
        "sqlalchemy.url": url,
        "sqlalchemy.echo": settings.DATABASE_ECHO,
    }

    if not is_sqlite:
        # Only add pool options for non-SQLite DBs
        configuration.update({
            "sqlalchemy.pool_size": settings.DATABASE_POOL_SIZE,
            "sqlalchemy.max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "sqlalchemy.pool_timeout": settings.DATABASE_POOL_TIMEOUT,
            "sqlalchemy.pool_recycle": settings.DATABASE_POOL_RECYCLE,
        })

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # This is fine for both SQLite and dev use
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
