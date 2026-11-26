from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import volumes_service as service
from domain.page_audits_schemas import CloseVolume
from domain.page_audits_service import close_volume, closure_readiness
from domain.volumes_model import volumes
from domain.volumes_schemas import ReceiveVolume

router = APIRouter()

@router.get('/volumes')
def list_volumes(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, volumes)


@router.post('/volumes/receive-volume')
def receive_volume(data: ReceiveVolume, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.receive_volume(conn, user, data)
        record(conn, user, 'volumes.receive_volume')
        return output


@router.get('/volumes/closure-readiness/{code}')
@router.get('/volumes/{code}/readiness')
@router.get('/volumes/{code}/closure-readiness')
@router.get('/closure_checks/{code}')
@router.get('/volume_closures/{code}')
@router.get('/closures/{code}')
def get_closure_readiness(code: str, user=Depends(actor)):
    with transaction() as conn:
        return closure_readiness(conn, code)


@router.post('/volumes/closure-readiness')
def post_closure_readiness(data: CloseVolume, user=Depends(actor)):
    with transaction() as conn:
        code = data.first('code', 'volume', 'volume_code')
        from core.records import need
        need(bool(code), '请提供要检查的册号')
        return closure_readiness(conn, str(code))


@router.post('/volumes/close-volume')
@router.post('/volumes/close')
def close_book(data: CloseVolume, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = close_volume(conn, user, data)
        record(conn, user, 'volumes.close_volume')
        return output


@router.post('/volumes/{code}/close-volume')
@router.post('/volumes/{code}/close')
def close_book_by_code(code: str, data: CloseVolume | None = None, user=Depends(actor)):
    allow(user, ('reviewer',))
    payload = (data or CloseVolume()).model_copy(update={'code': code})
    with transaction() as conn:
        output = close_volume(conn, user, payload)
        record(conn, user, 'volumes.close_volume')
        return output
