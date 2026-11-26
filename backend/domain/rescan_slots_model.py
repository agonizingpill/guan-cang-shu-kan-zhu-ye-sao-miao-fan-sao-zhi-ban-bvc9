from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


rescan_slots = Table('rescan_slots', metadata,
    Column('code', String(64), primary_key=True),
    Column('check_ref', String(64), ForeignKey('folio_checks.code'), nullable=False, unique=True),
    Column('bench', String(64), ForeignKey('scan_benches.code'), nullable=False),
    Column('day', String(64), nullable=False),
    Column('begin_at', Integer, nullable=False),
    Column('finish_at', Integer, nullable=False),
    Column('pages', JSON, nullable=False),
    Column('estimate', Float, nullable=False),
    Column('state', String(160), nullable=False),
    Column('token', String(64), nullable=False, unique=True),
    CheckConstraint('begin_at>=0'),
    CheckConstraint('finish_at<=1440'),
    CheckConstraint('begin_at<finish_at'),
    CheckConstraint("state in ('已预约','已交割')"),
)
