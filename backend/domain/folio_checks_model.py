from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


folio_checks = Table('folio_checks', metadata,
    Column('code', String(64), primary_key=True),
    Column('volume', String(64), ForeignKey('volumes.code'), nullable=False),
    Column('first', Integer, nullable=False),
    Column('last', Integer, nullable=False),
    Column('feed', String(64), nullable=False),
    Column('gutter', Float, nullable=False),
    Column('faults', JSON, nullable=False),
    CheckConstraint('first>=1'),
    CheckConstraint('last>=first'),
    CheckConstraint('gutter>=0'),
    CheckConstraint("feed in ('flat','cradle')"),
)
