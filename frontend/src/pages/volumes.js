        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "馆藏书刊扫描册档",
  "module": "馆藏册档",
  "caption": "馆藏册档",
  "detail": "登记在台书刊的确切页码范围。闭卷扫描册保留为计数参考。",
  "path": "/volumes",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "title",
      "label": "馆藏名称"
    },
    {
      "name": "first",
      "label": "起始页码"
    },
    {
      "name": "last",
      "label": "末页码"
    },
    {
      "name": "state",
      "label": "在架状态"
    }
  ],
  "layout": "split",
  "view": "grid",
  "actions": [
    {
      "name": "receive_volume",
      "label": "接收待扫馆藏",
      "path": "/volumes/receive-volume",
      "fields": [
        {
          "name": "code",
          "label": "馆藏册号",
          "kind": "text",
          "initial": "MS-011"
        },
        {
          "name": "title",
          "label": "馆藏名",
          "kind": "text",
          "initial": "《溪浦随刊》第11册"
        },
        {
          "name": "first",
          "label": "起页",
          "kind": "int",
          "initial": 1
        },
        {
          "name": "last",
          "label": "末页",
          "kind": "int",
          "initial": 128
        }
      ],
      "help": "册号会进入新图像的对应命名。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "volumes";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
