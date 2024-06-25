"""Create a baseline migrations

Revision ID: 39cb72e43a4b
Revises: 7a554827b77c
Create Date: 2024-06-23 18:22:32.033529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39cb72e43a4b'
down_revision: Union[str, None] = '7a554827b77c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
