from sqlalchemy import Boolean, CheckConstraint, Column, Float, ForeignKey, Integer, JSON, String, Table

from core.db import metadata


page_receipts = Table('page_receipts', metadata,
    Column('code', String(64), primary_key=True),
    Column('slot', String(64), ForeignKey('rescan_slots.code'), nullable=False, unique=True),
    Column('mapped_pages', JSON, nullable=False),
    Column('checked_by', String(64), nullable=False),
    Column('receipt_hash', String(64), nullable=False),
)
