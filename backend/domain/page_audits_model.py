from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    UniqueConstraint,
)

from core.db import metadata


# 抽查班的固定翻页名额。status/state 同时保留机器状态和界面中文状态。
audit_shifts = Table(
    'audit_shifts', metadata,
    Column('code', String(64), primary_key=True),
    Column('day', String(32), nullable=True),
    Column('volume', String(64), nullable=True),
    Column('quota', Integer, nullable=False),
    Column('status', String(16), nullable=False, server_default='open'),
    Column('state', String(32), nullable=False, server_default='排班中'),
    CheckConstraint('quota > 0', name='ck_audit_shifts_quota_positive'),
    CheckConstraint("status in ('open','closed')", name='ck_audit_shifts_status'),
    CheckConstraint("state in ('排班中','已结束')", name='ck_audit_shifts_state'),
)


# 每一行是本班派给复核员的一页；claim/report 都在同一行上推进。
page_audits = Table(
    'page_audits', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('code', String(64), nullable=False, unique=True),
    Column('shift', String(64), ForeignKey('audit_shifts.code'), nullable=False, index=True),
    Column('volume', String(64), ForeignKey('volumes.code'), nullable=False, index=True),
    Column('check_ref', String(64), ForeignKey('folio_checks.code'), nullable=False, index=True),
    Column('page', Integer, nullable=False),
    Column('risk', Float, nullable=False, server_default='0'),
    Column('status', String(16), nullable=False, server_default='pending', index=True),
    Column('state', String(32), nullable=False, server_default='待领取'),
    Column('result', String(16), nullable=True),
    Column('good', Boolean, nullable=True),
    Column('note', String(500), nullable=True),
    Column('claimed_by', String(255), nullable=True),
    Column('checked_by', String(255), nullable=True),
    Column('reviewer', String(255), nullable=True),
    UniqueConstraint('shift', 'check_ref', 'page', name='uq_page_audits_shift_check_page'),
    CheckConstraint('page >= 1', name='ck_page_audits_page_positive'),
    CheckConstraint('risk >= 0', name='ck_page_audits_risk_nonnegative'),
    CheckConstraint(
        "status in ('pending','claimed','good','bad')",
        name='ck_page_audits_status',
    ),
    CheckConstraint(
        "state in ('待领取','已领取','良好','坏页')",
        name='ck_page_audits_state',
    ),
    CheckConstraint("result is null or result in ('good','bad')", name='ck_page_audits_result'),
)


# 抽中漏记坏页后产生的重查单；同一页册段可因再次抽中而有多轮。
rechecks = Table(
    'rechecks', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('code', String(64), nullable=False, unique=True),
    Column('check_ref', String(64), ForeignKey('folio_checks.code'), nullable=False, index=True),
    Column('volume', String(64), ForeignKey('volumes.code'), nullable=False, index=True),
    Column('audit_code', String(64), nullable=True),
    Column('status', String(16), nullable=False, server_default='pending', index=True),
    Column('state', String(32), nullable=False, server_default='待重查'),
    Column('reason', String(500), nullable=True),
    Column('note', String(500), nullable=True),
    Column('requested_by', String(255), nullable=True),
    Column('reviewed_by', String(255), nullable=True),
    CheckConstraint("status in ('pending','passed')", name='ck_rechecks_status'),
    CheckConstraint("state in ('待重查','重查通过')", name='ck_rechecks_state'),
)
