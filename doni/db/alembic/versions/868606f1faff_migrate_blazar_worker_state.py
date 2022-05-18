"""empty message

Revision ID: 868606f1faff
Revises: f42680f49a77
Create Date: 2022-02-04 15:34:42.594220

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.automap import automap_base


# revision identifiers, used by Alembic.
revision = "868606f1faff"
down_revision = "f42680f49a77"
branch_labels = None
depends_on = None

Base = automap_base()


def _worker_task_model(bind):
    try:
        # SQLAlchemy >=1.4.0
        Base.prepare(autoload_with=bind)
    except:
        # SQLAlchemy <1.4.0
        Base.prepare(bind, reflect=True)
    return Base.classes.worker_task


def upgrade():
    """Update 'host' blazar worker fields to generic 'resource' naming."""
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    WorkerTask = _worker_task_model(bind)

    for wt in session.query(WorkerTask).filter(
        WorkerTask.worker_type == "blazar.physical_host"
    ):
        state_details = wt.state_details
        if "blazar_host_id" in state_details:
            state_details["blazar_resource_id"] = state_details["blazar_host_id"]
            del state_details["blazar_host_id"]
        if "host_created_at" in state_details:
            state_details["resource_created_at"] = state_details["host_created_at"]
            del state_details["host_created_at"]
        wt.state_details = state_details
        session.add(wt)
    session.commit()


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    WorkerTask = _worker_task_model(bind)

    for wt in session.query(WorkerTask).filter(
        WorkerTask.worker_type == "blazar.physical_host"
    ):  # type: worker_task
        state_details = wt.state_details
        if "blazar_resource_id" in state_details:
            state_details["blazar_host_id"] = state_details["blazar_resource_id"]
            del state_details["blazar_resource_id"]
        if "resource_created_at" in state_details:
            state_details["host_created_at"] = state_details["resource_created_at"]
            del state_details["resource_created_at"]
        wt.state_details = state_details
        session.add(wt)
    session.commit()
