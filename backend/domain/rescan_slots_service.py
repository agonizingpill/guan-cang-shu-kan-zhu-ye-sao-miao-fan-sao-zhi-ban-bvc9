from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.volumes_model import volumes
from domain.folio_checks_model import folio_checks
from domain.scan_benches_model import scan_benches
from domain.rescan_slots_model import rescan_slots
from domain.page_receipts_model import page_receipts


def estimate_count(conn, user, data):
    from domain.page_operations import schedule_payload
    return submit(user,schedule_payload(conn,data.check_ref))


def book_slot(conn, user, data):
    from domain.page_operations import reserve
    run=result(user,data.token)
    return reserve(conn,data,run)
