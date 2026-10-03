from alembic import context
from sqlalchemy import create_engine, pool
from shared.config import DATABASE_URL
from shared.db import Base
import shared.models  # noqa: register tables

def run():
    engine = create_engine(DATABASE_URL, poolclass=pool.NullPool)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
run()
