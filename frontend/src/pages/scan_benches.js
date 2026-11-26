        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "扫描台配置与开窗",
  "module": "扫描台值班窗",
  "caption": "扫描台值班窗",
  "detail": "槽架台和平台分别登记，预约时段必须完整落在开放分钟内。",
  "path": "/scan_benches",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "title",
      "label": "扫描台标识"
    },
    {
      "name": "feed",
      "label": "适用进页方式"
    },
    {
      "name": "opening",
      "label": "开始分钟"
    },
    {
      "name": "closing",
      "label": "结束分钟"
    },
    {
      "name": "one_page",
      "label": "每页占用分钟"
    },
    {
      "name": "ready",
      "label": "准入启用"
    }
  ],
  "layout": "flip",
  "view": "grid",
  "actions": [
    {
      "name": "set_access",
      "label": "登记扫描台当班状态",
      "path": "/scan_benches/set-access",
      "fields": [
        {
          "name": "code",
          "label": "扫描台",
          "kind": "text",
          "initial": "ST-CR"
        },
        {
          "name": "ready",
          "label": "本班启用",
          "kind": "bool",
          "initial": true
        }
      ],
      "help": "有待交割的预约时，须先完成预约才能停台。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "scan_benches";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
