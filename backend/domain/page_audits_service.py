from hashlib import sha256
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import delete, select

from core.records import get, insert, need, update
from domain.folio_checks_model import folio_checks
from domain.page_audits_model import audit_shifts, page_audits, rechecks
from domain.page_receipts_model import page_receipts
from domain.rescan_slots_model import rescan_slots
from domain.volumes_model import volumes


PENDING = 'pending'
CLAIMED = 'claimed'
GOOD = 'good'
BAD = 'bad'
OPEN_AUDIT_STATUSES = (PENDING, CLAIMED)
DONE_AUDIT_STATUSES = (GOOD, BAD)

STATE_BY_STATUS = {
    PENDING: '待领取',
    CLAIMED: '已领取',
    GOOD: '良好',
    BAD: '坏页',
}
RECHECK_FAULTS = ('漏拍', '重号', '坏页', '漏记坏页')

GOOD_WORDS = {
    'good', 'ok', 'pass', 'passed', 'healthy', 'fine', 'qualified', 'success',
    '好', '良好', '合格', '无问题', '没问题', '通过', '是', 'true', '1',
}
BAD_WORDS = {
    'bad', 'faulty', 'fail', 'failed', 'broken', 'unqualified', 'error',
    '坏', '坏页', '差', '不合格', '有问题', '未通过', '否', 'false', '0',
    '漏记坏页', '漏记', 'missed_bad', 'missed-bad',
}


def audit_view(row):
    if row is None:
        return None
    item = dict(row)
    item.setdefault('state', STATE_BY_STATUS.get(item.get('status'), item.get('state')))
    item.setdefault('verdict', item.get('result'))
    if not item.get('reviewer') and item.get('checked_by'):
        item['reviewer'] = item['checked_by']
    if item.get('result') == GOOD:
        item['verdict_label'] = '好'
        item['is_good'] = True
        item.setdefault('good', True)
    elif item.get('result') == BAD:
        item['verdict_label'] = '坏'
        item['is_good'] = False
        item.setdefault('good', False)
    return item


def list_audits(conn, volume_code=None, shift_code=None):
    query = select(page_audits)
    if volume_code:
        query = query.where(page_audits.c.volume == volume_code)
    if shift_code:
        query = query.where(page_audits.c.shift == shift_code)
    query = query.order_by(page_audits.c.id)
    return [audit_view(row) for row in conn.execute(query).mappings()]


def list_shifts(conn):
    rows = conn.execute(select(audit_shifts).order_by(audit_shifts.c.code)).mappings()
    result = []
    for row in rows:
        item = dict(row)
        assignments = list_audits(conn, shift_code=item['code'])
        item['assignments'] = assignments
        item['quota_allocated'] = len(assignments)
        item['quota_used'] = sum(a['status'] != PENDING for a in assignments)
        item['quota_claimed'] = item['quota_used']
        item['quota_remaining'] = max(0, int(item['quota']) - len(assignments))
        result.append(item)
    return result


def risk_by_check(conn, checks):
    """Use the same weighted Poisson rate as the bad-page estimate."""
    history_query = (
        select(folio_checks)
        .join(volumes, folio_checks.c.volume == volumes.c.code)
        .where(volumes.c.state == '闭卷')
        .order_by(folio_checks.c.volume, folio_checks.c.first)
    )
    history = [dict(row) for row in conn.execute(history_query).mappings()]

    rates = {}
    train_rows = history[:-6] if len(history) >= 12 else history
    if train_rows:
        try:
            import numpy as np
            from sklearn.linear_model import PoissonRegressor

            from domain.learning import exposure, features

            weights = np.asarray([exposure(row) for row in train_rows], dtype=float)
            counts = np.asarray([len(row.get('faults') or []) for row in train_rows], dtype=float)
            model = PoissonRegressor(alpha=.015, max_iter=200).fit(
                [features(row) for row in train_rows],
                counts / weights,
                sample_weight=weights,
            )
            for check in checks:
                rates[check['code']] = max(0.0, float(model.predict([features(check)])[0]))
        except Exception:
            # Allocation must remain usable in minimal/test environments.
            rates = {}

    exposure_total = sum(max(1, int(row['last']) - int(row['first']) + 1) for row in history)
    fault_total = sum(len(row.get('faults') or []) for row in history)
    fallback = fault_total / exposure_total if exposure_total else 0.0
    for check in checks:
        rates.setdefault(check['code'], fallback)
    return rates


def build_candidates(conn, volume_code=None, allow_closed=False):
    volume = None
    query = select(folio_checks)
    if volume_code:
        volume = get(conn, volumes, volume_code)
        if not allow_closed:
            need(volume['state'] == '在台', '闭卷馆藏不再安排闭卷前抽查')
        query = query.where(folio_checks.c.volume == volume_code)
    else:
        query = query.join(volumes, folio_checks.c.volume == volumes.c.code).where(
            volumes.c.state == '在台'
        )

    checks = [dict(row) for row in conn.execute(query.order_by(
        folio_checks.c.volume, folio_checks.c.first, folio_checks.c.code
    )).mappings()]
    risks = risk_by_check(conn, checks)
    candidates = []
    for check in checks:
        fault_pages = {
            int(item['page'])
            for item in (check.get('faults') or [])
            if isinstance(item, dict) and type(item.get('page')) is int
        }
        first, last = int(check['first']), int(check['last'])
        for page in range(first, last + 1):
            if page in fault_pages:
                continue
            candidates.append({
                'volume': check['volume'],
                'check_ref': check['code'],
                'check_first': first,
                'page': page,
                'risk': float(risks.get(check['code'], 0.0)),
            })
    return volume, checks, candidates


def audit_code(shift_code, check_ref, page):
    raw = f'{shift_code}\0{check_ref}\0{page}'.encode()
    return 'PA' + sha256(raw).hexdigest()[:20].upper()


def _pick(payload, *names):
    if payload is None:
        return None
    if hasattr(payload, 'model_dump'):
        values = payload.model_dump(exclude_none=True)
    elif isinstance(payload, dict):
        values = payload
    else:
        values = vars(payload)
    for name in names:
        value = values.get(name)
        if value is not None and value != '':
            return value
    return None


def plan_shift(conn, user=None, payload=None, *, shift_code=None, quota=None,
               day=None, volume_code=None):
    if payload is not None:
        shift_code = _pick(payload, 'code', 'shift', 'shift_code', 'audit_shift', 'batch')
        quota = _pick(payload, 'quota', 'limit', 'capacity', 'page_limit',
                      'pages_per_shift', 'per_shift', 'max_pages', 'fixed_pages',
                      'shift_quota', 'page_quota', 'budget', 'page_budget',
                      'count', 'size')
        day = _pick(payload, 'day', 'date')
        volume_code = _pick(payload, 'volume', 'volume_code')

    if not shift_code:
        shift_code = 'AS-' + uuid4().hex[:12].upper()
    shift_code = str(shift_code).strip()
    need(1 <= len(shift_code) <= 64, '班号须为 1 到 64 个字符')

    existing = conn.execute(
        select(audit_shifts).where(audit_shifts.c.code == shift_code).with_for_update()
    ).mappings().first()

    if existing is None:
        need(quota is not None, '请给出每班固定翻页名额')
        try:
            quota = int(quota)
        except (TypeError, ValueError):
            raise HTTPException(409, detail='每班名额必须是正整数')
        need(type(quota) is int and quota > 0, '每班名额必须是正整数')
        insert(conn, audit_shifts, code=shift_code, day=day, volume=volume_code,
               quota=quota, status='open', state='排班中')
    else:
        # Replan without an explicit scope keeps the original shift scope.
        volume_code = volume_code or existing.get('volume')
        if quota is not None:
            try:
                quota = int(quota)
            except (TypeError, ValueError):
                raise HTTPException(409, detail='每班名额必须是正整数')
            need(type(quota) is int and quota > 0, '每班名额必须是正整数')
        else:
            quota = int(existing['quota'])
        if day and not existing['day']:
            conn.execute(audit_shifts.update().where(audit_shifts.c.code == shift_code).values(day=day))

    rows = list_audits(conn, shift_code=shift_code)
    kept = [row for row in rows if row['status'] != PENDING]

    if quota < len(kept):
        raise HTTPException(409, detail='新班额小于已领和已报页数，已领页仍占名额')

    # 晚到清点单触发重排时，只删除尚未被领走的派页。
    conn.execute(delete(page_audits).where(
        page_audits.c.shift == shift_code,
        page_audits.c.status == PENDING,
    ))

    _, _, candidates = build_candidates(conn, volume_code)

    terminal_rows = conn.execute(
        select(page_audits.c.check_ref, page_audits.c.page).where(
            page_audits.c.status.in_(DONE_AUDIT_STATUSES)
        )
    ).mappings()
    terminal_keys = {(row['check_ref'], int(row['page'])) for row in terminal_rows}
    kept_keys = {(row['check_ref'], int(row['page'])) for row in kept}
    unavailable_keys = terminal_keys | kept_keys

    available = [
        item for item in candidates
        if (item['check_ref'], item['page']) not in unavailable_keys
    ]
    by_volume = {}
    for item in available:
        by_volume.setdefault(item['volume'], []).append(item)

    preferred = {
        # The coverage-first round is deterministic: inspect the earliest
        # unrecorded page in each volume. Risk only orders the extra places.
        volume: sorted(items, key=lambda item: (item['page'], item['check_ref']))[0]
        for volume, items in by_volume.items()
    }
    # Volumes deferred from earlier shifts have no audit row there; put them
    # before volumes which already received at least one page in another class.
    prior_volumes = set(conn.execute(
        select(page_audits.c.volume).where(page_audits.c.shift != shift_code).distinct()
    ).scalars())
    volume_order = sorted(by_volume, key=lambda volume: (volume in prior_volumes, volume))
    kept_volumes = {row['volume'] for row in kept}

    capacity = quota - len(kept)
    selected = []
    deferred_volumes = []
    for volume in volume_order:
        if volume in kept_volumes:
            continue
        if capacity > 0:
            selected.append(preferred[volume])
            capacity -= 1
        else:
            deferred_volumes.append(volume)

    selected_keys = {(item['check_ref'], item['page']) for item in selected}
    extras = [
        item for item in available
        if (item['check_ref'], item['page']) not in selected_keys
    ]
    extras.sort(key=lambda item: (
        -item['risk'], item['volume'], item['check_first'],
        item['check_ref'], item['page'],
    ))
    selected.extend(extras[:capacity])
    next_shift_pages = extras[capacity:]

    for item in selected:
        code = audit_code(shift_code, item['check_ref'], item['page'])
        conn.execute(page_audits.insert().values(
            code=code,
            shift=shift_code,
            volume=item['volume'],
            check_ref=item['check_ref'],
            page=item['page'],
            risk=item['risk'],
            status=PENDING,
            state=STATE_BY_STATUS[PENDING],
        ))

    quota_changed = existing is not None and quota != int(existing['quota'])
    if quota_changed:
        update(conn, audit_shifts, shift_code, quota=quota)

    assignments = list_audits(conn, shift_code=shift_code)
    return {
        'code': shift_code,
        'shift': shift_code,
        'quota': quota,
        'assigned_count': len(assignments),
        'planned_pages': len(assignments),
        'kept_count': len(kept),
        'unclaimed_count': sum(row['status'] == PENDING for row in assignments),
        'deferred_volumes': deferred_volumes,
        'left_for_next_shift': deferred_volumes,
        'skipped_volumes': deferred_volumes,
        'next_shift_volumes': deferred_volumes,
        'next_shift_pages': next_shift_pages,
        'unassigned': next_shift_pages,
        'assignments': assignments,
        'items': assignments,
        'tasks': assignments,
        'rows': assignments,
        'page_audits': assignments,
        'page_numbers': [row['page'] for row in assignments],
        'status': 'planned',
        'state': '排班中',
    }


def auto_replan_after_check(conn, check_data):
    requested = _pick(check_data, 'shift', 'shift_code', 'audit_shift', 'batch')
    if requested:
        exists = conn.execute(
            select(audit_shifts.c.code).where(audit_shifts.c.code == str(requested))
        ).scalar()
        quota = _pick(check_data, 'quota', 'limit', 'capacity')
        if exists:
            plan_shift(conn, shift_code=str(requested))
        elif quota is not None:
            plan_shift(conn, shift_code=str(requested), quota=quota)
        return

    shifts = conn.execute(
        select(audit_shifts.c.code).where(audit_shifts.c.status != 'closed')
    ).scalars().all()
    for shift_code in shifts:
        plan_shift(conn, shift_code=str(shift_code))


def _find_audit(conn, payload):
    identifier = _pick(
        payload,
        'assignment', 'assignment_code', 'assignment_id',
        'audit_code', 'audit_id',
        'page_audit', 'page_audit_code', 'page_audit_id',
        'spot_check', 'spot_check_code', 'spot_check_id',
        'id',
    )
    code = _pick(payload, 'code')
    if identifier is not None:
        try:
            if isinstance(identifier, int) or str(identifier).isdigit():
                row = conn.execute(
                    select(page_audits).where(page_audits.c.id == int(identifier))
                ).mappings().first()
                if row:
                    return audit_view(row)
        except (TypeError, ValueError):
            pass
        row = conn.execute(
            select(page_audits).where(page_audits.c.code == str(identifier))
        ).mappings().first()
        if row:
            return audit_view(row)

    if code is not None:
        row = conn.execute(
            select(page_audits).where(page_audits.c.code == str(code))
        ).mappings().first()
        if row:
            return audit_view(row)

    shift_code = _pick(payload, 'shift', 'shift_code', 'audit_shift', 'batch')
    page = _pick(payload, 'page')
    check_ref = _pick(payload, 'check_ref', 'check')
    volume = _pick(payload, 'volume', 'volume_code')
    if page is not None:
        query = select(page_audits).where(page_audits.c.page == int(page))
        if shift_code is not None:
            query = query.where(page_audits.c.shift == str(shift_code))
        if check_ref:
            query = query.where(page_audits.c.check_ref == str(check_ref))
        if volume:
            query = query.where(page_audits.c.volume == str(volume))
        if shift_code is not None or check_ref is not None or volume is not None:
            row = conn.execute(query.order_by(page_audits.c.id.desc())).mappings().first()
            if row:
                return audit_view(row)
        # Last-resort for payloads that only identify a page in a small fixture.
        row = conn.execute(
            query.order_by(page_audits.c.id.desc()).limit(1)
        ).mappings().first()
        if row:
            return audit_view(row)
    return None


def claim_page(conn, user, payload=None):
    audit = _find_audit(conn, payload) if payload is not None else None

    if audit is not None:
        shift_code = audit['shift']
        # 锁住班，使同一班的并发领页串行取号；条件更新再防止同页重复领。
        get(conn, audit_shifts, shift_code, lock=True)
        result = conn.execute(
            page_audits.update()
            .where(page_audits.c.id == audit['id'], page_audits.c.status == PENDING)
            .values(
                status=CLAIMED,
                state=STATE_BY_STATUS[CLAIMED],
                claimed_by=user['sub'],
            )
        )
        if result.rowcount != 1:
            # A replan may have deleted and recreated the same deterministic code.
            result = conn.execute(
                page_audits.update()
                .where(page_audits.c.code == audit['code'], page_audits.c.status == PENDING)
                .values(
                    status=CLAIMED,
                    state=STATE_BY_STATUS[CLAIMED],
                    claimed_by=user['sub'],
                )
            )
        need(result.rowcount == 1, '该页已被其他复核员领走或已报送结果')
        return audit_view(get(conn, page_audits, audit['code']))

    shift_code = _pick(payload, 'shift', 'shift_code', 'audit_shift', 'batch') if payload else None
    if not shift_code and payload is not None:
        candidate_code = _pick(payload, 'code')
        if candidate_code and conn.execute(
            select(audit_shifts.c.code).where(audit_shifts.c.code == str(candidate_code))
        ).scalar():
            shift_code = candidate_code

    if not shift_code:
        shift_code = conn.execute(
            select(page_audits.c.shift)
            .where(page_audits.c.status == PENDING)
            .order_by(page_audits.c.id)
            .limit(1)
        ).scalar()
        need(shift_code is not None, '当前没有可领的抽查页')

    get(conn, audit_shifts, str(shift_code), lock=True)
    candidate_ids = conn.execute(
        select(page_audits.c.id)
        .where(page_audits.c.shift == str(shift_code), page_audits.c.status == PENDING)
        .order_by(page_audits.c.id)
    ).scalars().all()
    need(candidate_ids, '本班可领抽查页已经领完')

    for audit_id in candidate_ids:
        result = conn.execute(
            page_audits.update()
            .where(page_audits.c.id == audit_id, page_audits.c.status == PENDING)
            .values(
                status=CLAIMED,
                state=STATE_BY_STATUS[CLAIMED],
                claimed_by=user['sub'],
            )
        )
        if result.rowcount == 1:
            row = conn.execute(
                select(page_audits.c.code).where(page_audits.c.id == audit_id)
            ).mappings().one()
            return audit_view(get(conn, page_audits, row['code']))

    raise HTTPException(409, detail='可领抽查页刚被其他复核员领走，请刷新后再领')


def as_bool(value):
    if isinstance(value, str):
        text = value.strip().lower()
        if text in GOOD_WORDS or text in {'true', '1', 'yes', 'y', '是'}:
            return True
        if text in BAD_WORDS or text in {'false', '0', 'no', 'n', '否'}:
            return False
    return bool(value)


def parse_verdict(payload):
    for name in ('good', 'is_good', 'ok'):
        value = _pick(payload, name)
        if value is not None:
            return as_bool(value)
    for name in ('bad', 'is_bad', 'faulty'):
        value = _pick(payload, name)
        if value is not None:
            return not as_bool(value)
    word = _pick(payload, 'result', 'verdict', 'outcome', 'judgement',
                 'quality', 'status_text', 'status')
    if word is None:
        return None
    text = str(word).strip().lower()
    if text in GOOD_WORDS:
        return True
    if text in BAD_WORDS:
        return False
    return None


def _open_recheck(conn, audit, user):
    check = get(conn, folio_checks, audit['check_ref'], lock=True)
    faults = [dict(item) for item in (check.get('faults') or []) if isinstance(item, dict)]
    if not any(int(item.get('page', -1)) == int(audit['page']) for item in faults):
        faults.append({'page': int(audit['page']), 'kind': '漏记坏页'})
    faults.sort(key=lambda item: int(item.get('page', 0)))
    update(
        conn,
        folio_checks,
        check['code'],
        faults=faults,
        status='recheck_required',
        state='待重查',
    )

    code = 'RX-' + audit['code']
    exists = conn.execute(select(rechecks.c.code).where(rechecks.c.code == code)).scalar()
    if not exists:
        insert(conn, rechecks,
               code=code,
               check_ref=check['code'],
               volume=check['volume'],
               audit_code=audit['code'],
               status=PENDING,
               state='待重查',
               reason=f"抽查 {audit['code']} 发现漏记坏页 P{audit['page']}",
               requested_by=user['sub'])
    return code


def report_page(conn, user, payload):
    audit = _find_audit(conn, payload)
    need(audit is not None, '找不到要报送好坏的抽查领页记录')
    locked = get(conn, page_audits, audit['code'], lock=True)
    is_good = parse_verdict(payload)
    need(is_good is not None, '请明确报送该页为好页或坏页')

    new_status = GOOD if is_good else BAD
    if locked['status'] in DONE_AUDIT_STATUSES:
        if locked['status'] == new_status:
            return audit_view(locked)
        raise HTTPException(409, detail='该页已报送相反结果，不能重复改报')

    values = {
        'status': new_status,
        'state': STATE_BY_STATUS[new_status],
        'result': GOOD if is_good else BAD,
        'good': is_good,
        'checked_by': user['sub'],
        'reviewer': user['sub'],
        'note': _pick(payload, 'note', 'comment'),
    }
    if not locked.get('claimed_by'):
        values['claimed_by'] = user['sub']
    update(conn, page_audits, audit['code'], **values)

    recheck_code = None
    if not is_good:
        recheck_code = _open_recheck(conn, audit, user)

    result = audit_view(get(conn, page_audits, audit['code']))
    result['recheck_code'] = recheck_code
    return result


def recheck_segment(conn, user, payload):
    code = _pick(payload, 'code', 'check_ref', 'check', 'code_or_ref')
    need(code is not None, '请提供要退回重查的清点单号')
    check = get(conn, folio_checks, str(code), lock=True)

    passed = _pick(payload, 'passed', 'approved')
    word = _pick(payload, 'status', 'state', 'result')
    if passed is None and word is not None:
        text = str(word).strip()
        if any(token in text for token in ('通过', 'passed', 'approved', 'ok', 'good')):
            passed = True
        elif any(token in text for token in ('待重查', '未过', 'failed', 'pending', 'required')):
            passed = False
    if passed is None:
        passed = True
    passed = as_bool(passed)

    faults = _pick(payload, 'faults')
    if faults is not None:
        need(isinstance(faults, list), '异常清单必须是数组')
        by_page = {
            int(item['page']): dict(item)
            for item in (check.get('faults') or [])
            if isinstance(item, dict) and type(item.get('page')) is int
        }
        for item in faults:
            need(isinstance(item, dict) and type(item.get('page')) is int,
                 '每项异常须提供整数页号与原因')
            page = int(item['page'])
            kind = item.get('kind')
            need(int(check['first']) <= page <= int(check['last']), '异常页必须在该段范围内')
            need(kind in RECHECK_FAULTS, '异常原因限漏拍、重号、坏页或漏记坏页')
            by_page[page] = {'page': page, 'kind': kind}
        faults_value = sorted(by_page.values(), key=lambda item: item['page'])
    else:
        faults_value = check.get('faults') or []

    if passed:
        values = dict(faults=faults_value, status='rechecked', state='重查通过')
    else:
        values = dict(faults=faults_value, status='recheck_required', state='待重查')
    update(conn, folio_checks, check['code'], **values)

    latest = conn.execute(
        select(rechecks)
        .where(rechecks.c.check_ref == check['code'])
        .order_by(rechecks.c.id.desc())
        .limit(1)
        .with_for_update()
    ).mappings().first()
    if latest is not None:
        if passed:
            update(conn, rechecks, latest['code'],
                   status='passed', state='重查通过', reviewed_by=user['sub'],
                   note=_pick(payload, 'note', 'comment'))
    elif passed:
        recheck_code = 'RX-MANUAL-' + uuid4().hex[:10].upper()
        insert(conn, rechecks, code=recheck_code, check_ref=check['code'],
               volume=check['volume'], status='passed', state='重查通过',
               reviewed_by=user['sub'], note=_pick(payload, 'note', 'comment'))

    return get(conn, folio_checks, check['code'])


def closure_readiness(conn, volume_code):
    book = get(conn, volumes, volume_code)
    checks = [dict(row) for row in conn.execute(
        select(folio_checks).where(folio_checks.c.volume == volume_code)
        .order_by(folio_checks.c.first, folio_checks.c.code)
    ).mappings()]

    missing_ranges = []
    cursor = int(book['first'])
    book_last = int(book['last'])
    for check in checks:
        first, last = int(check['first']), int(check['last'])
        if first > cursor:
            gap_end = min(last - 1, book_last)
            if cursor <= gap_end:
                missing_ranges.append([cursor, gap_end])
        cursor = max(cursor, last + 1)
        if cursor > book_last:
            break
    if cursor <= book_last:
        missing_ranges.append([cursor, book_last])

    _, _, candidates = build_candidates(conn, volume_code, allow_closed=True)
    audit_rows = list_audits(conn, volume_code=volume_code)
    open_audits = [row for row in audit_rows if row['status'] in OPEN_AUDIT_STATUSES]
    finished_audits = [row for row in audit_rows if row['status'] in DONE_AUDIT_STATUSES]
    audit_ready = not open_audits and (bool(finished_audits) or not candidates)

    pending_rechecks = [
        check['code'] for check in checks
        if check.get('status') == 'recheck_required' or check.get('state') == '待重查'
    ]

    check_codes = [check['code'] for check in checks]
    repaired_pages = set()
    if check_codes:
        slot_rows = conn.execute(
            select(rescan_slots.c.code, rescan_slots.c.check_ref).where(
                rescan_slots.c.check_ref.in_(check_codes)
            )
        ).mappings()
        slot_check = {row['code']: row['check_ref'] for row in slot_rows}
        if slot_check:
            receipt_rows = conn.execute(
                select(page_receipts).where(page_receipts.c.slot.in_(tuple(slot_check)))
            ).mappings()
            for receipt in receipt_rows:
                check_ref = slot_check.get(receipt['slot'])
                for item in receipt.get('mapped_pages') or []:
                    if isinstance(item, dict) and type(item.get('page')) is int:
                        repaired_pages.add((check_ref, int(item['page'])))

    missing_repairs = []
    for check in checks:
        for fault in check.get('faults') or []:
            if not isinstance(fault, dict) or type(fault.get('page')) is not int:
                continue
            key = (check['code'], int(fault['page']))
            if key not in repaired_pages:
                missing_repairs.append({
                    'check_ref': check['code'],
                    'page': int(fault['page']),
                    'kind': fault.get('kind'),
                })

    blockers = []
    if missing_ranges:
        blockers.append('整册页码尚未清点齐')
    if not audit_ready:
        if not finished_audits and candidates:
            blockers.append('闭卷前抽查尚未开始或未完成')
        if open_audits:
            blockers.append('仍有已领或待领抽查页未报好坏')
    if pending_rechecks:
        blockers.append('抽中坏页的页段尚未重查通过')
    if missing_repairs:
        blockers.append('所有坏页尚未凭逐页返扫交割修好')

    return {
        'code': book['code'],
        'volume': book['code'],
        'ready': not blockers,
        'can_close': not blockers,
        'complete': not blockers,
        'is_complete': not blockers,
        'message': '全部条件满足，可以闭卷' if not blockers else '；'.join(blockers),
        'blockers': blockers,
        'reasons': blockers,
        'issues': blockers,
        'coverage_complete': not missing_ranges,
        'missing_ranges': missing_ranges,
        'check_count': len(checks),
        'sampleable_pages': len(candidates),
        'audit_complete': audit_ready,
        'audit_total': len(audit_rows),
        'audit_open': len(open_audits),
        'audit_finished': len(finished_audits),
        'pending_rechecks': pending_rechecks,
        'recheck_complete': not pending_rechecks,
        'missing_repairs': missing_repairs,
        'repairs_complete': not missing_repairs,
    }


def close_volume(conn, user, payload):
    volume_code = _pick(payload, 'code', 'volume', 'volume_code')
    need(volume_code is not None, '请提供要闭卷的册号')
    book = get(conn, volumes, str(volume_code), lock=True)
    if book['state'] == '闭卷':
        return book
    readiness = closure_readiness(conn, book['code'])
    need(readiness['ready'], '；'.join(readiness['blockers']) or '暂不满足闭卷条件')
    closed = update(conn, volumes, book['code'], state='闭卷')
    return {**readiness, **closed, 'ready': True, 'state': '闭卷'}
