"""hardware_loosen_name_constraint

Revision ID: f42680f49a77
Revises: 4c500cc3c90d
Create Date: 2021-03-25 10:28:27.520157

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f42680f49a77"
down_revision = "4c500cc3c90d"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("uniq_hardware0name", "hardware", type_="unique")
    op.create_unique_constraint(
        "uniq_hardware0name0deleted", "hardware", ["name", "deleted"]
    )


def downgrade():
    op.drop_constraint("uniq_hardware0name0deleted", "hardware", type_="unique")
    op.create_unique_constraint("uniq_hardware0name", "hardware", ["name"])
