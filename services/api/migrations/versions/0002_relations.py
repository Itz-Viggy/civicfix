"""Enforce ownership and content references, including databases from early local builds."""
from alembic import op
from sqlalchemy import inspect
revision='0002'
down_revision='0001'
branch_labels=None
depends_on=None

def upgrade():
    for table,column,target in [('drafts','owner','sessions'),('photos','draft_id','drafts'),('analysis_jobs','draft_id','drafts')]:
        if not inspect(op.get_bind()).get_foreign_keys(table):
            with op.batch_alter_table(table) as batch:
                batch.create_foreign_key('fk_'+table+'_'+column,target,[column],['id'])

def downgrade():
    pass  # Keep integrity constraints when reverting application metadata revision.
