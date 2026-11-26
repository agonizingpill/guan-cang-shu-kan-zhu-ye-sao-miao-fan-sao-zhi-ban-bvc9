# 馆藏书刊逐页扫描返扫值班

蒲页市立馆数字化室维护逐册扫描页序、补扫台时与图像替换凭证。

## 现场工作与联系人

蒲页市立馆数字化室为七名馆员处理地方刊物。早班逐册核对页号，以往用纸单圈出漏拍页，并在共享表格手写台位。复核记录有时跨页段，扫描台会排重，改图后也难定位原页。系统从实体册与原机图号的校核结论出发，给晚班安排返扫台时，再把页号和新图的对应关系交给编目馆员。

- 馆藏册档 `volumes`，字段为 `title`（馆藏名称）、`first`（起始页码）、`last`（末页码）、`state`（在架状态）。模型约束位于 `backend/domain/volumes_model.py`，规则位于 `volumes_service.py`。
- 页段顺序清点 `folio_checks`，字段为 `volume`（扫描册档）、`first`（段起页）、`last`（段末页）、`feed`（进页方式）、`gutter`（书槽深度 mm）、`faults`（页码异常清单）。模型约束位于 `backend/domain/folio_checks_model.py`，规则位于 `folio_checks_service.py`。
- 扫描台值班窗 `scan_benches`，字段为 `title`（扫描台标识）、`feed`（适用进页方式）、`opening`（开始分钟）、`closing`（结束分钟）、`one_page`（每页占用分钟）、`ready`（准入启用）。模型约束位于 `backend/domain/scan_benches_model.py`，规则位于 `scan_benches_service.py`。
- 页段返扫值班单 `rescan_slots`，字段为 `check_ref`（页序清点号）、`bench`（占用扫描台）、`day`（值班日期）、`begin_at`（开始分钟）、`finish_at`（结束分钟）、`pages`（逐页待返扫表）、`estimate`（预算坏页数）、`state`（值班状态）、`token`（预测凭证）。模型约束位于 `backend/domain/rescan_slots_model.py`，规则位于 `rescan_slots_service.py`。
- 逐页返扫交割 `page_receipts`，字段为 `slot`（已预约值班单）、`mapped_pages`（原页号与新图编号）、`checked_by`（复核员）、`receipt_hash`（逐页凭证 SHA-256）。模型约束位于 `backend/domain/page_receipts_model.py`，规则位于 `page_receipts_service.py`。
- 闭卷前抽查 `audit_shifts` / `page_audits` / `rechecks`：班次固定翻页名额、按册保底一页后依坏页模型页风险派页、复核员原子领页并报送好坏；漏记坏页会追加到 `folio_checks.faults` 并把该段置为待重查。闭卷就绪规则位于 `backend/domain/page_audits_service.py`。

### 一天的业务操作

1. 08:20 入台核对 MS-010 的起末页与册号。
2. 08:40 封存 101–120 页清点单 QC-101，记录漏拍 103、116 页和重号 109 页。
3. 09:10 以历史 24 个页段按有效页数估计返扫工量。
4. 09:25 槽架台第 600–635 分钟预约给 RS-101。
5. 09:50 第二段预约同台冲突，改排第 635–665 分钟。
6. 10:40 交割夹带第二段页码时被拒。
7. 11:00 复核推荐命名对应的三个 TIFF 图码，签收 RC-101。

## 启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

打开 `http://127.0.0.1:18315`。FastAPI OpenAPI 在 `http://127.0.0.1:19315/docs`。
Compose 运行 Nginx、Python FastAPI、独立 Redis 消费进程、MySQL 8 和 Redis，SQL 与 Redis 使用命名卷。
本地开发可在 Python 3.11 环境安装 `backend/requirements.txt` 后从 backend 目录运行 `uvicorn core.app:app`。须提供 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`，`SEED_DEMO` 控制演示初始化。

| 演示账号 | 权限 |
|---|---|
| operator@demo.test | 收册、封存逐段页号核对记录、发起坏页计数 |
| reviewer@demo.test | 根据计数凭证确认台时、开关扫描台、核验逐页映射 |
| viewer@demo.test | 查看册档、异常清单、值班单与交割记录 |

三个本地演示账号均使用 `DemoC0de!2026`。角色在 `backend/core/roles.py` 和 `frontend/src/store.js` 中声明。计算状态在 worker、queueing、API 和前端表单中使用。进页方式 `flat` 和 `cradle` 定义在 `backend/domain/page_operations.py`、两张 SQL 业务表及前端表单默认值中。

## 页面与接口

| 业务任务 | FastAPI 路由 | 页面 |
|---|---|---|
| 馆藏册档 | `/volumes` /volumes/receive-volume | `frontend/src/pages/volumes.js` |
| 页段顺序清点 | `/folio_checks` /folio_checks/mark-faults | `frontend/src/pages/folio_checks.js` |
| 扫描台值班窗 | `/scan_benches` /scan_benches/set-access | `frontend/src/pages/scan_benches.js` |
| 页段返扫值班单 | `/rescan_slots` /rescan_slots/estimate-count，/rescan_slots/book-slot | `frontend/src/pages/rescan_slots.js` |
| 逐页返扫交割 | `/page_receipts` /page_receipts/accept-pages | `frontend/src/pages/page_receipts.js` |
| 闭卷抽查与闭卷 | `/page_audits`，/page_audits/plan-shift、/claim-page、/report-page，/folio_checks/recheck，/volumes/close-volume | `frontend/src/pages/spot_checks.js` |

SQL 实体与约束在 `backend/domain` 下维护。前端使用原生 ES modules。核心算子为 PoissonRegressor。训练目标为逐段坏页数除以该段曝光页数，拟合时以曝光页数作样本权重；返回期望坏页数、六段末段留出偏差与输入哈希。

使用模拟馆藏元数据与扫描记录。系统核验页号及 TIFF 编号，由馆员检查实际图像和实物页。

[MIT](LICENSE)
