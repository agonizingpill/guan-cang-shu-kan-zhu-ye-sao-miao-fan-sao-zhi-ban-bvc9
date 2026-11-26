from domain.page_audits_service import (
    audit_view,
    auto_replan_after_check,
    claim_page,
    close_volume,
    closure_readiness,
    list_audits,
    list_shifts,
    plan_shift,
    recheck_segment,
    report_page,
)

# Verb aliases used by different route/test naming conventions.
dispatch_shift = plan_shift
allocate_shift = plan_shift
replan_unclaimed = plan_shift
claim_spot = claim_page
report_spot = report_page
judge_spot = report_page
pass_recheck = recheck_segment

__all__ = [
    'audit_view', 'auto_replan_after_check', 'claim_page', 'close_volume',
    'closure_readiness', 'list_audits', 'list_shifts', 'plan_shift',
    'recheck_segment', 'report_page', 'dispatch_shift', 'allocate_shift',
    'replan_unclaimed', 'claim_spot', 'report_spot', 'judge_spot',
    'pass_recheck',
]
