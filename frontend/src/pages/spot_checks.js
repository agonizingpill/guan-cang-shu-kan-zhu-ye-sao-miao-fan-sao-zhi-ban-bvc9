import {workspace} from '../workspace.js';

const page = {
  title: '闭卷抽查页面',
  module: '闭卷前抽查与准闭卷',
  caption: '闭卷前抽查派页',
  detail: '每班先给每册派一页，其余名额按坏页模型的页风险排序。晚到清点单只重排待领取页；已领页继续检查并占用班额。',
  path: '/page_audits',
  columns: [
    {name: 'code', label: '抽查页号'},
    {name: 'shift', label: '班次'},
    {name: 'volume', label: '馆藏册号'},
    {name: 'check_ref', label: '清点单号'},
    {name: 'page', label: '抽查页码'},
    {name: 'risk', label: '页风险'},
    {name: 'state', label: '领报状态'},
    {name: 'claimed_by', label: '领页复核员'},
    {name: 'checked_by', label: '报结果复核员'},
  ],
  layout: 'split',
  view: 'table',
  actions: [
    {
      name: 'plan_shift',
      label: '按班额派页或重排',
      path: '/page_audits/plan-shift',
      fields: [
        {name: 'code', label: '班次号', kind: 'text', initial: 'AS-20261126-A'},
        {name: 'quota', label: '本班最多翻页', kind: 'int', initial: 8},
        {name: 'day', label: '值班日期', kind: 'text', initial: '2026-11-26', required: false},
        {name: 'volume', label: '只限某册（可空）', kind: 'text', initial: '', required: false},
      ],
      help: '先保每册一页，再按 Poisson 坏页模型的每页风险派剩余名额；未入选册页留给下一班。',
      roles: ['operator', 'reviewer'],
      success: '已派页',
    },
    {
      name: 'claim_page',
      label: '复核员领下一页',
      path: '/page_audits/claim-page',
      fields: [
        {name: 'shift', label: '班次号', kind: 'text', initial: 'AS-20261126-A'},
      ],
      help: '两人同时领取会由数据库条件更新分配到不同页；本班名额领完即拒绝。',
      roles: ['reviewer'],
      success: '已领页',
    },
    {
      name: 'report_page',
      label: '报送抽查页好坏',
      path: '/page_audits/report-page',
      fields: [
        {name: 'code', label: '抽查页号', kind: 'text', initial: ''},
        {name: 'good', label: '该页是否完好', kind: 'bool', initial: true},
        {name: 'note', label: '备注（可空）', kind: 'text', initial: '', required: false},
      ],
      help: '选择“否”即报坏页；若该页不在原异常清单，会自动记为漏记坏页并退回对应页段重查。',
      roles: ['reviewer'],
      success: '已报送',
    },
    {
      name: 'recheck_segment',
      label: '页段重查通过',
      path: '/folio_checks/recheck',
      fields: [
        {name: 'code', label: '清点单号', kind: 'text', initial: 'QC-101'},
        {name: 'passed', label: '重查是否通过', kind: 'bool', initial: true},
      ],
      help: '抽中漏记坏页后，该页段须重新清点并在此确认通过。',
      roles: ['operator', 'reviewer'],
      success: '重查结果已写入',
    },
    {
      name: 'closure_readiness',
      label: '检查闭卷条件',
      path: '/volumes/closure-readiness',
      fields: [
        {name: 'code', label: '馆藏册号', kind: 'text', initial: 'MS-010'},
      ],
      help: '列出清点覆盖、未报抽查页、待通过重查和未修复坏页。',
      roles: ['operator', 'reviewer'],
      success: '检查完成',
    },
    {
      name: 'close_volume',
      label: '核验条件并闭卷',
      path: '/volumes/close-volume',
      fields: [
        {name: 'code', label: '馆藏册号', kind: 'text', initial: 'MS-010'},
      ],
      help: '整册清点齐、抽查页全部报完、退回页段重查通过、所有坏页有返扫交割后才可闭卷。',
      roles: ['reviewer'],
      success: '已闭卷',
    },
  ],
};

export const {title} = page;
export const key = 'spot_checks';
export async function render(root, role) {
  await workspace(root, role, page);
}
