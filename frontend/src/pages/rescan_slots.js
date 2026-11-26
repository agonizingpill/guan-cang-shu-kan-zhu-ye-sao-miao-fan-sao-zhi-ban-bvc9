        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "计量并预约返扫时段",
  "module": "页段返扫值班单",
  "caption": "页段返扫值班单",
  "detail": "Poisson 回归按页数估计复扫工作量。实际返扫对象仍取逐页异常清单。",
  "path": "/rescan_slots",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "check_ref",
      "label": "页序清点号"
    },
    {
      "name": "bench",
      "label": "占用扫描台"
    },
    {
      "name": "day",
      "label": "值班日期"
    },
    {
      "name": "begin_at",
      "label": "开始分钟"
    },
    {
      "name": "finish_at",
      "label": "结束分钟"
    },
    {
      "name": "pages",
      "label": "逐页待返扫表"
    },
    {
      "name": "estimate",
      "label": "预算坏页数"
    },
    {
      "name": "state",
      "label": "值班状态"
    },
    {
      "name": "token",
      "label": "预测凭证"
    }
  ],
  "layout": "split",
  "view": "table",
  "actions": [
    {
      "name": "estimate_count",
      "label": "估算页段工作量",
      "path": "/rescan_slots/estimate-count",
      "fields": [
        {
          "name": "check_ref",
          "label": "清点号",
          "kind": "text",
          "initial": "QC-101"
        }
      ],
      "help": "按历史曝光页数加权并保留末段验证。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "book_slot",
      "label": "锁定返扫台时",
      "path": "/rescan_slots/book-slot",
      "fields": [
        {
          "name": "code",
          "label": "预约号",
          "kind": "text",
          "initial": "RS-101"
        },
        {
          "name": "token",
          "label": "计数预测凭证",
          "kind": "token",
          "initial": ""
        },
        {
          "name": "bench",
          "label": "扫描台",
          "kind": "text",
          "initial": "ST-CR"
        },
        {
          "name": "day",
          "label": "值班日期 YYYY-MM-DD",
          "kind": "text",
          "initial": "2026-11-24"
        },
        {
          "name": "begin_at",
          "label": "开始分钟",
          "kind": "int",
          "initial": 600
        },
        {
          "name": "finish_at",
          "label": "结束分钟",
          "kind": "int",
          "initial": 635
        }
      ],
      "help": "值班台时须覆盖预测向上取整与已知坏页中的较大值。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "rescan_slots";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
