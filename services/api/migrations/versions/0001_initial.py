"""Initial private session/draft/photo/job storage."""
revision='0001'
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    from alembic import op
    from civicfix.storage import Base
    Base.metadata.create_all(op.get_bind())
def downgrade():
    from alembic import op
    from civicfix.storage import Base
    Base.metadata.drop_all(op.get_bind())
