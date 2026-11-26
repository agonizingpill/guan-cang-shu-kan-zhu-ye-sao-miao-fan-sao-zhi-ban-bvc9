from domain.page_audits_model import audit_shifts, page_audits, rechecks

# The same workflow is described in some call sites as “spot checks”.
spot_check_shifts = audit_shifts
spot_checks = page_audits
spot_check_rechecks = rechecks

__all__ = [
    'audit_shifts',
    'page_audits',
    'rechecks',
    'spot_check_shifts',
    'spot_checks',
    'spot_check_rechecks',
]
