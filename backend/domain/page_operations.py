from datetime import date
from hashlib import sha256
import json
from re import fullmatch

from sqlalchemy import select

from core.records import get, insert, need, update
from domain.folio_checks_model import folio_checks
from domain.page_receipts_model import page_receipts
from domain.rescan_slots_model import rescan_slots
from domain.scan_benches_model import scan_benches
from domain.volumes_model import volumes

FAULTS = ('漏拍', '重号')
FEEDS = ('cradle', 'flat')


def volume_code(code):
    need(fullmatch(r'[A-Z][A-Z0-9-]{2,23}', code) is not None, '册号或返扫号须为 3 到 24 位英文大写、数字或连字符')


def record_check(conn, data):
    book = get(conn, volumes, data.volume, lock=True)
    volume_code(data.code)
    need(book['state']=='在台', '闭卷馆藏只可作为历史读数')
    need(book['first']<=data.first<=data.last<=book['last'] and data.last-data.first<100,
         '页段必须在实体册的页码范围内，每段至多 100 页')
    need(data.feed in FEEDS and 0<=data.gutter<=20, '校对进页方式与实测书槽深度')
    need(isinstance(data.faults, list), '异常清单必须是数组')
    page_numbers = set()
    for item in data.faults:
        need(isinstance(item, dict) and set(item)=={'page','kind'} and type(item['page']) is int,
             '每项异常须提供整数页号与原因')
        page = item['page']
        need(data.first<=page<=data.last and item['kind'] in FAULTS and page not in page_numbers,
             '异常必须是段内未重复页号，原因限漏拍和重号')
        page_numbers.add(page)
    clash = select(folio_checks.c.code).where(folio_checks.c.volume==book['code'],
        folio_checks.c.first<=data.last, folio_checks.c.last>=data.first).limit(1)
    need(conn.execute(clash).scalar() is None, '同册页段重叠，沿用原清点单')
    return insert(conn, folio_checks, **(data.model_dump() | {'faults':sorted(data.faults,key=lambda item:item['page'])}))


def change_access(conn, data):
    bench = get(conn, scan_benches, data.code, lock=True)
    if not data.ready:
        query = select(rescan_slots.c.code).where(rescan_slots.c.bench==data.code,
            rescan_slots.c.state=='已预约').limit(1).with_for_update()
        need(conn.execute(query).scalar() is None, '扫描台仍有未交割返扫单')
    if bench['ready']==data.ready:
        return bench
    return update(conn, scan_benches, data.code, ready=data.ready)


def schedule_payload(conn, code):
    check = get(conn, folio_checks, code)
    book = get(conn, volumes, check['volume'])
    need(book['state']=='在台', '仅在台页段可安排返扫')
    need(bool(check['faults']), '干净页段无需预约返扫')
    query = select(folio_checks).join(volumes, folio_checks.c.volume==volumes.c.code).where(
        volumes.c.state=='闭卷').order_by(folio_checks.c.volume, folio_checks.c.first)
    rows = [dict(row) for row in conn.execute(query).mappings()]
    need(len(rows)>=12 and sum(len(row['faults']) for row in rows[:-6])>0, '闭卷参考不足以估计页序问题')
    return {'check':check, 'history':rows}


def reserve(conn, data, task):
    volume_code(data.code)
    try:
        day = date.fromisoformat(data.day)
    except ValueError:
        day = None
    need(day is not None and day.isoformat()==data.day, '值班日期须为 YYYY-MM-DD')
    bench = get(conn, scan_benches, data.bench, lock=True)
    check = get(conn, folio_checks, task['input']['check']['code'], lock=True)
    need(bench['ready'] and bench['feed']==check['feed'], '扫描台须启用且允许该进页方式')
    need(bench['opening']<=data.begin_at<data.finish_at<=bench['closing'], '选定的台时必须在当班开放窗口内')
    model = task['result']
    pages = [item['page'] for item in check['faults']]
    need(data.finish_at-data.begin_at>=bench['one_page']*max(len(pages),model['planned_pages']), '台时不足以返扫')
    exists = select(rescan_slots.c.code).where(rescan_slots.c.check_ref==check['code']).with_for_update()
    need(conn.execute(exists).scalar() is None, '该页段已有返扫预约')
    clashes = select(rescan_slots.c.code).where(
        rescan_slots.c.bench==bench['code'], rescan_slots.c.day==data.day,
        rescan_slots.c.begin_at<data.finish_at, rescan_slots.c.finish_at>data.begin_at).limit(1).with_for_update()
    need(conn.execute(clashes).scalar() is None, '扫描台已被预约，请选其他时隙')
    return insert(conn, rescan_slots, **data.model_dump(), check_ref=check['code'], pages=pages,
                  estimate=model['expected_count'], state='已预约')


def receive_pages(conn, user, data):
    volume_code(data.code)
    slot = get(conn, rescan_slots, data.slot, lock=True)
    need(slot['state']=='已预约', '只有已预约且未交割的值班单可签收')
    check = get(conn, folio_checks, slot['check_ref'])
    mapping = data.mapped_pages
    need(isinstance(mapping,list) and all(
        isinstance(item,dict) and set(item)=={'page','asset'} and type(item['page']) is int
        for item in mapping), '逐页清单须列出原页号和新图编号')
    mapping = sorted(mapping,key=lambda item:item['page'])
    need([item['page'] for item in mapping]==slot['pages'], '交割必须完整匹配逐页清单')
    for item in mapping:
        expected = f"{check['volume']}-{slot['code']}-P{item['page']:04}.tif"
        need(item['asset']==expected, '新图编号必须引用同一馆藏、值班单和原页号')
    receipt = insert(conn, page_receipts, code=data.code, slot=slot['code'], mapped_pages=mapping,
                     checked_by=user['sub'],
                     receipt_hash=sha256(json.dumps(mapping,sort_keys=True).encode()).hexdigest())
    update(conn, rescan_slots, slot['code'], state='已交割')
    return receipt
