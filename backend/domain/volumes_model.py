from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


volumes = Table('volumes', metadata,
    Column('code', String(64), primary_key=True),
    Column('title', String(160), nullable=False),
    Column('first', Integer, nullable=False),
    Column('last', Integer, nullable=False),
    Column('state', String(160), nullable=False),
    CheckConstraint('first>=1'),
    CheckConstraint('last>=first'),
    CheckConstraint("state in ('在台','闭卷')"),
)
