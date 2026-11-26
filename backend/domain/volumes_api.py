from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import volumes_service as service
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
