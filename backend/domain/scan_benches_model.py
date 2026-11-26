from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


scan_benches = Table('scan_benches', metadata,
    Column('code', String(64), primary_key=True),
    Column('title', String(160), nullable=False),
    Column('feed', String(64), nullable=False),
    Column('opening', Integer, nullable=False),
    Column('closing', Integer, nullable=False),
    Column('one_page', Integer, nullable=False),
    Column('ready', Boolean, nullable=False),
    CheckConstraint('opening>=0'),
    CheckConstraint('closing<=1440'),
    CheckConstraint('opening<closing'),
    CheckConstraint('one_page between 1 and 15'),
)
