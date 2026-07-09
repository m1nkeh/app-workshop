from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config
from sqlalchemy import pool

# Reuse db.py so migrations connect the same way the app does.
import db

# Alembic's Config object, backed by alembic.ini.
config = context.config

# Set up logging from alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No ORM models -- migrations are hand-written DDL, so no autogenerate target.
target_metadata = None


def run_migrations_offline() -> None:
    """Run in 'offline' mode: emit SQL to the script output, no live connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run in 'online' mode: connect and apply migrations directly."""
    # connectable = engine_from_config(
    #     config.get_section(config.config_ini_section, {}),
    #     prefix="sqlalchemy.",
    #     poolclass=pool.NullPool,
    # )

    # db.py's engine handles env-aware token auth; skip the setup above.
    connectable = db.make_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
