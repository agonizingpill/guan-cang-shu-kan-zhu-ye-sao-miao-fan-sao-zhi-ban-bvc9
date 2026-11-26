from domain.page_audits_schemas import (
    ClaimPage,
    CloseVolume,
    PlanShift,
    RecheckSegment,
    ReportPage,
)

DispatchShift = PlanShift
ClaimSpot = ClaimPage
ReportSpot = ReportPage

__all__ = [
    'ClaimPage', 'CloseVolume', 'PlanShift', 'RecheckSegment', 'ReportPage',
    'DispatchShift', 'ClaimSpot', 'ReportSpot',
]
