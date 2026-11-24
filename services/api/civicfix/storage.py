from pathlib import Path
import os
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, event, text
from sqlalchemy.orm import declarative_base,Session
Base=declarative_base()
class SessionRow(Base):
    __tablename__='sessions'
    id=Column(String,primary_key=True)
    csrf=Column(String,nullable=False)
    expires=Column(Float,nullable=False)
    feedback_window_start = Column(Float)
    feedback_count = Column(Integer, nullable=False, server_default=text('0'))
class DraftRow(Base):
    __tablename__='drafts'
    id=Column(String,primary_key=True)
    owner=Column(String,ForeignKey('sessions.id'),index=True,nullable=False)
    expires=Column(Float,index=True,nullable=False)
    content=Column(Text,nullable=False)
class PhotoRow(Base):
    __tablename__='photos'
    id=Column(String,primary_key=True)
    draft_id=Column(String,ForeignKey('drafts.id'),index=True,nullable=False)
    key=Column(String,nullable=False)
class JobRow(Base):
    __tablename__='analysis_jobs'
    id=Column(String,primary_key=True)
    draft_id=Column(String,ForeignKey('drafts.id'),index=True,nullable=False)
    content=Column(Text,nullable=False)


class FeedbackRow(Base):
    __tablename__ = 'feedback'
    __table_args__ = (
        UniqueConstraint('job_id', 'kind', name='uq_feedback_job_kind'),
        UniqueConstraint('draft_id', 'kind', name='uq_feedback_draft_kind'),
    )

    id = Column(Integer, primary_key=True)
    kind = Column(String, nullable=False)
    created_at = Column(Float, nullable=False, index=True)
    simulated = Column(Boolean, nullable=False)
    job_id = Column(String, ForeignKey('analysis_jobs.id', ondelete='SET NULL'))
    draft_id = Column(String, ForeignKey('drafts.id', ondelete='SET NULL'))
    verdict = Column(String)
    predicted_category = Column(String)
    suggested_category = Column(String)
    model_id = Column(String)
    model_revision = Column(String)
    prompt_version = Column(String)
    rating = Column(Integer)
    comment = Column(Text)


class Store:
    def __init__(self,path):
        self.path=Path(path).resolve(); self.path.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.photos=self.path/'photos'; self.photos.mkdir(exist_ok=True,mode=0o700)
        os.chmod(self.path,0o700); os.chmod(self.photos,0o700)
        self.engine=create_engine(f'sqlite:///{self.path/"civicfix.sqlite3"}',connect_args={'check_same_thread':False,'timeout':10})
        @event.listens_for(self.engine,'connect')
        def pragma(conn,_):
            conn.execute('PRAGMA foreign_keys=ON'); conn.execute('PRAGMA journal_mode=WAL'); conn.execute('PRAGMA secure_delete=ON')
        from alembic.config import Config
        from alembic import command
        config=Config()
        config.set_main_option('script_location',str(Path(__file__).resolve().parents[1]/'migrations'))
        with self.engine.begin() as connection:
            config.attributes['connection']=connection
            command.upgrade(config,'head')
    def session(self): return Session(self.engine)
    def checkpoint(self):
        with self.engine.connect() as c: c.exec_driver_sql('PRAGMA wal_checkpoint(TRUNCATE)')
