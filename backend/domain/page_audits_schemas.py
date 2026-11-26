from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class FlexibleModel(BaseModel):
    """接受业务别名；核心服务用 _pick() 从这些名称中取第一个非空值。"""

    model_config = ConfigDict(extra='allow', populate_by_name=True)

    def first(self, *names: str) -> Any:
        values = self.model_dump(exclude_none=True)
        for name in names:
            value = values.get(name)
            if value is not None and value != '':
                return value
        return None


class PlanShift(FlexibleModel):
    code: Any = None
    shift: Any = None
    shift_code: Any = None
    audit_shift: Any = None
    batch: Any = None
    day: Any = None
    date: Any = None
    quota: Any = None
    limit: Any = None
    capacity: Any = None
    page_limit: Any = None
    pages_per_shift: Any = None
    per_shift: Any = None
    max_pages: Any = None
    fixed_pages: Any = None
    shift_quota: Any = None
    page_quota: Any = None
    budget: Any = None
    page_budget: Any = None
    count: Any = None
    size: Any = None
    volume: Any = None
    volume_code: Any = None


class ClaimPage(FlexibleModel):
    code: Any = None
    shift: Any = None
    shift_code: Any = None
    audit_shift: Any = None
    batch: Any = None
    assignment: Any = None
    assignment_code: Any = None
    assignment_id: Any = None
    audit_code: Any = None
    audit_id: Any = None
    page_audit: Any = None
    page_audit_code: Any = None
    page_audit_id: Any = None
    spot_check: Any = None
    spot_check_code: Any = None
    spot_check_id: Any = None
    id: Any = None
    page: Any = None
    check_ref: Any = None
    check: Any = None
    volume: Any = None
    volume_code: Any = None


class ReportPage(ClaimPage):
    result: Any = None
    verdict: Any = None
    outcome: Any = None
    judgement: Any = None
    quality: Any = None
    status_text: Any = None
    good: Any = None
    bad: Any = None
    is_good: Any = None
    is_bad: Any = None
    ok: Any = None
    passed: Any = None
    faulty: Any = None
    note: Any = None
    comment: Any = None


class RecheckSegment(FlexibleModel):
    code: Any = None
    check_ref: Any = None
    check: Any = None
    code_or_ref: Any = None
    passed: Any = None
    approved: Any = None
    status: Any = None
    state: Any = None
    result: Any = None
    note: Any = None
    comment: Any = None
    faults: Any = None
    reviewer: Any = None


class CloseVolume(FlexibleModel):
    code: Any = None
    volume: Any = None
    volume_code: Any = None
    note: Any = None
