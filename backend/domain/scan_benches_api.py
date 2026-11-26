from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import scan_benches_service as service
from domain.scan_benches_model import scan_benches
from domain.scan_benches_schemas import SetAccess

router = APIRouter()

@router.get('/scan_benches')
def list_scan_benches(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, scan_benches)


@router.post('/scan_benches/set-access')
def set_access(data: SetAccess, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.set_access(conn, user, data)
        record(conn, user, 'scan_benches.set_access')
        return output
