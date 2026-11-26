from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.volumes_model import volumes
from domain.folio_checks_model import folio_checks
from domain.scan_benches_model import scan_benches
from domain.rescan_slots_model import rescan_slots
from domain.page_receipts_model import page_receipts


def set_access(conn, user, data):
    from domain.page_operations import change_access
    return change_access(conn,data)
