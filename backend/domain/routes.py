from domain.volumes_api import router as volumes
from domain.folio_checks_api import router as folio_checks
from domain.scan_benches_api import router as scan_benches
from domain.rescan_slots_api import router as rescan_slots
from domain.page_receipts_api import router as page_receipts
from domain.page_audits_api import router as page_audits

routers = (
    volumes,
    folio_checks,
    scan_benches,
    rescan_slots,
    page_receipts,
    page_audits,
)
