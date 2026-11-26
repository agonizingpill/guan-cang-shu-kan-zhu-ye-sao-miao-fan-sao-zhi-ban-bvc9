from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import folio_checks_service as service
from domain.folio_checks_model import folio_checks
from domain.folio_checks_schemas import MarkFaults

router = APIRouter()

@router.get('/folio_checks')
def list_folio_checks(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, folio_checks)


@router.post('/folio_checks/mark-faults')
def mark_faults(data: MarkFaults, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.mark_faults(conn, user, data)
        record(conn, user, 'folio_checks.mark_faults')
        return output
