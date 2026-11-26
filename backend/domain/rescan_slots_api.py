from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import rescan_slots_service as service
from domain.rescan_slots_model import rescan_slots
from domain.rescan_slots_schemas import EstimateCount, BookSlot

router = APIRouter()

@router.get('/rescan_slots')
def list_rescan_slots(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, rescan_slots)


@router.post('/rescan_slots/estimate-count')
def estimate_count(data: EstimateCount, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.estimate_count(conn, user, data)
        record(conn, user, 'rescan_slots.estimate_count')
        return output


@router.post('/rescan_slots/book-slot')
def book_slot(data: BookSlot, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.book_slot(conn, user, data)
        record(conn, user, 'rescan_slots.book_slot')
        return output
