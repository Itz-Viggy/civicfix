from alembic import context
from sqlalchemy import create_engine
from civicfix.storage import Base
config=context.config
connection=config.attributes.get('connection')
if connection is not None:
    context.configure(connection=connection,target_metadata=Base.metadata)
    with context.begin_transaction():context.run_migrations()
else:
    from civicfix.config import load_config
    from pathlib import Path
    path=Path(load_config().data_dir).resolve();path.mkdir(parents=True,exist_ok=True)
    engine=create_engine(f'sqlite:///{path/"civicfix.sqlite3"}')
    with engine.connect() as connection:
        context.configure(connection=connection,target_metadata=Base.metadata)
        with context.begin_transaction():context.run_migrations()
