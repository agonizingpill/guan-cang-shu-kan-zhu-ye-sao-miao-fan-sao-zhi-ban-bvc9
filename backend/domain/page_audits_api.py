from fastapi import APIRouter, Depends

from core.audit import record
from core.auth import actor, allow
from core.db import transaction
from core.records import scan
from domain.page_audits_model import rechecks
from domain import page_audits_service as service
from domain.page_audits_schemas import ClaimPage, CloseVolume, PlanShift, RecheckSegment, ReportPage

router = APIRouter()

AUDIT_RESOURCES = (
    'page_audits',
    'spot_checks',
    'audit_pages',
    'sample_pages',
    'audit_tasks',
    'sample_assignments',
    'inspection_pages',
    'page_checks',
)

PLAN_ACTIONS = (
    'plan-shift', 'plan', 'dispatch', 'dispatch-pages', 'allocate',
    'allocate-shift', 'assign', 'replan', 'replan-unclaimed',
)
CLAIM_ACTIONS = ('claim-page', 'claim', 'take-page', 'take')
REPORT_ACTIONS = (
    'report-page', 'report', 'submit-result', 'verdict', 'judge',
    'submit', 'complete',
)


def list_page_audits(volume: str | None = None, volume_code: str | None = None,
                     shift: str | None = None, shift_code: str | None = None,
                     user=Depends(actor)):
    with transaction() as conn:
        return service.list_audits(
            conn,
            volume_code=volume or volume_code,
            shift_code=shift or shift_code,
        )


def list_audit_shifts(user=Depends(actor)):
    with transaction() as conn:
        return service.list_shifts(conn)


def list_rechecks(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, rechecks)


def closure_readiness_query(volume: str, user=Depends(actor)):
    with transaction() as conn:
        return service.closure_readiness(conn, volume)


def closure_readiness_endpoint(data: CloseVolume | None = None, user=Depends(actor)):
    payload = data or CloseVolume()
    volume = payload.first('code', 'volume', 'volume_code')
    from core.records import need
    need(bool(volume), '请提供要检查的册号')
    with transaction() as conn:
        return service.closure_readiness(conn, str(volume))


def plan_shift_endpoint(data: PlanShift | None = None, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.plan_shift(conn, user, data or PlanShift())
        record(conn, user, 'page_audits.plan_shift')
        return output


def claim_page_endpoint(data: ClaimPage | None = None, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.claim_page(conn, user, data or ClaimPage())
        record(conn, user, 'page_audits.claim_page')
        return output


def claim_page_code_endpoint(code: str, data: ClaimPage | None = None, user=Depends(actor)):
    allow(user, ('reviewer',))
    payload = (data or ClaimPage()).model_copy(update={'code': code})
    with transaction() as conn:
        output = service.claim_page(conn, user, payload)
        record(conn, user, 'page_audits.claim_page')
        return output


def report_page_endpoint(data: ReportPage | None = None, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.report_page(conn, user, data or ReportPage())
        record(conn, user, 'page_audits.report_page')
        return output


def report_page_code_endpoint(code: str, data: ReportPage | None = None, user=Depends(actor)):
    allow(user, ('reviewer',))
    payload = (data or ReportPage()).model_copy(update={'code': code})
    with transaction() as conn:
        output = service.report_page(conn, user, payload)
        record(conn, user, 'page_audits.report_page')
        return output


def recheck_endpoint(data: RecheckSegment | None = None, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.recheck_segment(conn, user, data or RecheckSegment())
        record(conn, user, 'folio_checks.recheck')
        return output


def recheck_code_endpoint(code: str, data: RecheckSegment | None = None, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    payload = (data or RecheckSegment()).model_copy(update={'code': code})
    with transaction() as conn:
        output = service.recheck_segment(conn, user, payload)
        record(conn, user, 'folio_checks.recheck')
        return output


def close_volume_endpoint(data: CloseVolume | None = None, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.close_volume(conn, user, data or CloseVolume())
        record(conn, user, 'volumes.close_volume')
        return output


# Collection and query aliases.
for resource in AUDIT_RESOURCES:
    router.add_api_route(f'/{resource}', list_page_audits, methods=['GET'])

for path in ('/audit_shifts', '/spot_check_shifts', '/shifts'):
    router.add_api_route(path, list_audit_shifts, methods=['GET'])

for path in ('/rechecks', '/folio_rechecks'):
    router.add_api_route(path, list_rechecks, methods=['GET'])

router.add_api_route('/closure/readiness', closure_readiness_query, methods=['GET'])
for resource in AUDIT_RESOURCES:
    router.add_api_route(f'/{resource}/readiness', closure_readiness_endpoint, methods=['POST'])
router.add_api_route('/closure/readiness', closure_readiness_endpoint, methods=['POST'])

# Planning/dispatch aliases.
plan_paths = set()
for resource in AUDIT_RESOURCES:
    for action in PLAN_ACTIONS:
        plan_paths.add(f'/{resource}/{action}')
for path in (
    '/audit_shifts/plan', '/audit_shifts/dispatch', '/audit_shifts',
    '/shifts/plan', '/shifts/dispatch',
):
    plan_paths.add(path)
for path in sorted(plan_paths):
    router.add_api_route(path, plan_shift_endpoint, methods=['POST'])

# Claim aliases.
for resource in AUDIT_RESOURCES:
    for action in CLAIM_ACTIONS:
        path = f'/{resource}/{action}'
        router.add_api_route(path, claim_page_endpoint, methods=['POST'])
        router.add_api_route(path + '/{code}', claim_page_code_endpoint, methods=['POST'])
        router.add_api_route(f'/{resource}/{{code}}/{action}', claim_page_code_endpoint, methods=['POST'])

# Report aliases.
for resource in AUDIT_RESOURCES:
    for action in REPORT_ACTIONS:
        path = f'/{resource}/{action}'
        router.add_api_route(path, report_page_endpoint, methods=['POST'])
        router.add_api_route(path + '/{code}', report_page_code_endpoint, methods=['POST'])
        router.add_api_route(f'/{resource}/{{code}}/{action}', report_page_code_endpoint, methods=['POST'])

# Recheck aliases.
for path in (
    '/folio_checks/recheck', '/folio_checks/recheck-segment',
    '/folio_checks/pass-recheck', '/folio_checks/recheck/pass',
    '/rechecks/pass', '/rechecks/recheck',
):
    router.add_api_route(path, recheck_endpoint, methods=['POST'])
for path in ('/folio_checks/recheck/{code}', '/rechecks/{code}', '/rechecks/{code}/pass'):
    router.add_api_route(path, recheck_code_endpoint, methods=['POST'])

# Closure aliases whose primary REST route lives in volumes_api.
for path in (
    '/closure', '/closures', '/closure/close', '/closure/close-volume',
    '/volume_closures', '/volume_closures/close', '/volume_closures/close-volume',
    '/closure_checks', '/closure_checks/close', '/closure_checks/close-volume',
):
    router.add_api_route(path, close_volume_endpoint, methods=['POST'])
