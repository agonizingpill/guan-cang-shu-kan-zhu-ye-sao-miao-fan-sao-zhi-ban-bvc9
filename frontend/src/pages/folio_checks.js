        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "逐段页序校核",
  "module": "页段顺序清点",
  "caption": "页段顺序清点",
  "detail": "校对馆藏册页码与位次，留存漏拍和重号清单。记录一段后禁止再用相同物理页段建另一张清点单。",
  "path": "/folio_checks",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "volume",
      "label": "扫描册档"
    },
    {
      "name": "first",
      "label": "段起页"
    },
    {
      "name": "last",
      "label": "段末页"
    },
    {
      "name": "feed",
      "label": "进页方式"
    },
    {
      "name": "gutter",
      "label": "书槽深度 mm"
    },
    {
      "name": "faults",
      "label": "页码异常清单"
    }
  ],
  "layout": "flip",
  "view": "table",
  "actions": [
    {
      "name": "mark_faults",
      "label": "封存页号异常",
      "path": "/folio_checks/mark-faults",
      "fields": [
        {
          "name": "code",
          "label": "段清点号",
          "kind": "text",
          "initial": "QC-101"
        },
        {
          "name": "volume",
          "label": "馆藏册号",
          "kind": "text",
          "initial": "MS-010"
        },
        {
          "name": "first",
          "label": "起始页",
          "kind": "int",
          "initial": 101
        },
        {
          "name": "last",
          "label": "结束页",
          "kind": "int",
          "initial": 120
        },
        {
          "name": "feed",
          "label": "进页方式 flat/cradle",
          "kind": "text",
          "initial": "cradle"
        },
        {
          "name": "gutter",
          "label": "书槽深度 mm",
          "kind": "float",
          "initial": 6
        },
        {
          "name": "faults",
          "label": "逐页漏拍或重号",
          "kind": "json",
          "initial": [
            {
              "page": 103,
              "kind": "漏拍"
            },
            {
              "page": 109,
              "kind": "重号"
            },
            {
              "page": 116,
              "kind": "漏拍"
            }
          ]
        }
      ],
      "help": "录入起末页码以及明确发现的每一页。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "folio_checks";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
