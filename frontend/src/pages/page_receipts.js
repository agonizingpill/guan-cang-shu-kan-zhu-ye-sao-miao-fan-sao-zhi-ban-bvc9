        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "逐页新图交割",
  "module": "逐页返扫交割",
  "caption": "逐页返扫交割",
  "detail": "逐页核对原馆藏页和 TIFF 新图。缺一页、混入另一页段或同一页交两次都不能销号。",
  "path": "/page_receipts",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "slot",
      "label": "已预约值班单"
    },
    {
      "name": "mapped_pages",
      "label": "原页号与新图编号"
    },
    {
      "name": "checked_by",
      "label": "复核员"
    },
    {
      "name": "receipt_hash",
      "label": "逐页凭证 SHA-256"
    }
  ],
  "layout": "stack",
  "view": "table",
  "actions": [
    {
      "name": "accept_pages",
      "label": "扫描馆员复核交割",
      "path": "/page_receipts/accept-pages",
      "fields": [
        {
          "name": "code",
          "label": "交割号",
          "kind": "text",
          "initial": "RC-101"
        },
        {
          "name": "slot",
          "label": "预约号",
          "kind": "text",
          "initial": "RS-101"
        },
        {
          "name": "mapped_pages",
          "label": "页码和新 TIFF",
          "kind": "json",
          "initial": [
            {
              "page": 103,
              "asset": "MS-010-RS-101-P0103.tif"
            },
            {
              "page": 109,
              "asset": "MS-010-RS-101-P0109.tif"
            },
            {
              "page": 116,
              "asset": "MS-010-RS-101-P0116.tif"
            }
          ]
        }
      ],
      "help": "核对实际返扫页与命名清单，保存页映射哈希。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "page_receipts";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
