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
    Column('status', String(16), nullable=False, server_default='checked'),
    Column('state', String(32), nullable=False, server_default='已核对'),
    CheckConstraint('first>=1'),
    CheckConstraint('last>=first'),
    CheckConstraint('gutter>=0'),
    CheckConstraint("feed in ('flat','cradle')"),
    CheckConstraint("status in ('checked','recheck_required','rechecked')"),
    CheckConstraint("state in ('已核对','待重查','重查通过')"),
)
