from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import page_receipts_service as service
from domain.page_receipts_model import page_receipts
from domain.page_receipts_schemas import AcceptPages

router = APIRouter()

@router.get('/page_receipts')
def list_page_receipts(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, page_receipts)


@router.post('/page_receipts/accept-pages')
def accept_pages(data: AcceptPages, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.accept_pages(conn, user, data)
        record(conn, user, 'page_receipts.accept_pages')
        return output
