## 🤖 Assistant

以下为“可直接交付研发/测试”的 PRD 正文稿（含字段表、状态机、页面交互要点、导出字段清单、接口草案）。你可复制到你们的 PRD 模板中按需改公司抬头/术语即可。

---

# 自动对账系统 PRD（MVP v1.0）

## 0. 文档信息
- 版本：v1.0
- 业务口径：以入库单口径对账
- 关键字段：PO号 / 物料编码（映射到内部物料编码）/ 数量（整数）/ 含税单价（4位小数）
- 数据源：供应商对账单 Excel + 内部“标准对账导出表”（含内部物料编码+名称/规格）

---

## 1. 背景与目标
### 1.1 背景
- 供应商Excel格式差异大（表头、字段名、分隔符、前缀等），且供应商物料编码与内部物料编码不一定一致，导致人工对账耗时且易错。
- 需要通过“模板映射 + 物料清洗 + 物料对照表 + 自动匹配（含聚合）+ 差异闭环”实现自动化。

### 1.2 目标（Goals）
- 自动解析供应商Excel → 标准化字段 → 与内部标准对账数据匹配（支持 1:1、1:N、N:1）。
- 输出可审计结果：匹配明细、差异明细、汇总统计、证据留存。
- 形成闭环：采购在差异页可建立“供应商物料→内部物料”映射，提高后续自动匹配率。

### 1.3 不做（Out of scope）
- 不回写 ERP/财务系统
- 不做 OCR/PDF 识别
- 不做按供应商差异化容差（一期统一容差）

---

## 2. 角色与权限
### 2.1 角色
- 采购（Buyer）：创建对账任务、上传文件、配置模板（仅本供应商）、维护本供应商物料对照表、处理差异、导出。
- 管理员（Admin，可选）：全局参数配置、查看全量任务、维护异常数据治理（若你们需要）。

### 2.2 数据可见性
- 采购默认仅可见：自己创建的任务（或自己负责供应商的任务——若你们有供应商归属表，可在实现时扩展）。
- 物料对照表：采购仅维护自己供应商（supplier_id 维度隔离）。

---

## 3. 数据口径与校验规则（强约束）
### 3.1 数量 qty
- 必须为整数。
- 允许解析 `10.0` → 10；不允许 `10.5`（标记 data_invalid）。
- 允许千分位、空格；解析时需清除。

### 3.2 含税单价 unit_price_tax
- 统一保留 **4 位小数**：`unit_price_tax_std = round(unit_price_tax, 4)`
- 用于匹配、聚合、展示的标准字段均采用 unit_price_tax_std。

### 3.3 PO号
- 不需要特殊清洗（按你确认）。
- 仍需 trim 去空格、去不可见字符（基础清洗）。

### 3.4 物料编码
- 必须支持按供应商配置清洗规则（见 6.2）。
- 必须支持供应商物料对照表（见 6.3）。

---

## 4. 流程概述（端到端）
1) 采购创建对账任务（选择供应商、期间）  
2) 系统拉取内部“标准对账导出表”并生成任务快照  
3) 采购上传供应商Excel，选择模板（已有）或新建模板  
4) 模板配置：列映射 + 物料编码清洗链 +（启用）物料对照表  
5) 执行对账：先标准化→映射物料→1:1匹配→聚合匹配→生成结果  
6) 采购处理差异：备注/附件/状态流转；对“物料未映射”可直接建对照并重跑  
7) 导出报表与证据包；系统留存6个月

---

## 5. 任务状态机（State Machine）
### 5.1 Task 状态
| 状态 | 含义 | 触发动作 |
|---|---|---|
| DRAFT 待上传 | 已创建任务，未上传供应商文件 | 创建任务 |
| UPLOADED 已上传 | 已上传文件并解析成功 | 上传并解析通过 |
| MAPPING_READY 待映射确认 | 模板映射可用、可预览校验 | 选择/配置模板 |
| RECONCILING 对账中 | 引擎运行中 | 执行对账 |
| DONE 对账完成 | 已生成匹配/差异结果 | 对账完成 |
| CLOSED 已关闭 | 差异处理完毕/人工关闭 | 手动关闭 |
| VOID 作废 | 任务无效 | 手动作废 |

> 允许 DONE 状态下反复“重跑对账”（更新映射/对照表后）。

### 5.2 Issue（差异）状态
| 状态 | 含义 |
|---|---|
| OPEN 待确认 |
| IN_PROGRESS 处理中 |
| RESOLVED 已解决（待关闭） |
| CLOSED 已关闭 |

---

## 6. 核心规则（匹配、聚合、物料映射）
### 6.1 容差参数（全局）
- qty_tolerance：默认 0（数量整数）
- price_tolerance：建议默认 0.0001（可配置）
- amount_tolerance：建议默认 0.01（可配置，用于金额舍入差）

### 6.2 物料编码清洗链（按供应商模板配置）
**输入：** supplier_item_code_raw  
**输出：** supplier_item_code_clean

支持配置的操作（按顺序执行）：
1. trim / 去不可见字符
2. 大小写统一（如统一大写）
3. 全半角统一
4. 删除分隔符（可选集合：`-` `_` 空格 `/` `.`）
5. 去前缀/后缀（支持 startsWith/endsWith；可扩展正则）
6. 前导零策略（保留/去除）

### 6.3 供应商物料对照表命中优先级（固定）
将供应商行转换为 internal_item_code：
1) 若对照表命中（supplier_id + supplier_item_code_clean/raw）且 status=启用 → internal_item_code  
2) 否则若 supplier_item_code_clean 与 internal_item_code 等值命中内部标准表 → internal_item_code  
3) 否则：差异类型 `material_unmapped`

### 6.4 匹配引擎（分层）
**Step 0：标准化**
- 供应商侧：列映射→清洗→物料映射→得到 internal_item_code、qty(int)、unit_price_tax_std(4)
- 内部侧：从任务快照读取并标准化 unit_price_tax_std、qty(int)

**Step 1：1:1 匹配（优先）**
匹配条件：
- PO 相等
- internal_item_code 相等
- abs(供应商单价_std - 内部单价_std) ≤ price_tolerance
- abs(数量差) ≤ qty_tolerance

标记：match_type=ONE_TO_ONE

**Step 2：聚合匹配（解决 1:N、N:1）**
分组 key：
- (PO, internal_item_code, unit_price_tax_std)

聚合字段：
- sum_qty
- sum_calc_amount = sum(qty * unit_price_tax_std)

聚合判定：
- abs(v_sum_qty - i_sum_qty) ≤ qty_tolerance
- abs(v_sum_calc_amount - i_sum_calc_amount) ≤ amount_tolerance

标记：match_type=AGGREGATE，并保存关联明细集合（可展开查看行列表）。

**Step 3：未匹配/异常分类**
- material_unmapped：物料未映射（优先让采购处理）
- only_vendor：供应商多出
- only_internal：内部多出
- qty_diff / price_diff / amount_diff（用于已定位到同key但数值不一致的场景）
- data_invalid：关键字段缺失/非法

---

## 7. 页面与交互（MVP）
### 7.1 任务列表页
- 筛选：供应商、期间、状态
- 列：任务ID、供应商、期间、创建人、创建时间、状态、匹配行数/差异行数（完成后显示）
- 操作：进入详情、作废、导出（完成后）

### 7.2 任务详情页
- 区块1：内部快照概览（内部行数、金额合计等）
- 区块2：供应商文件（上传/替换、解析状态、原文件下载）
- 区块3：模板（选择已有模板/新建模板、当前版本）
- 操作：预览标准化结果、执行对账、重跑对账、关闭任务
- Tab：匹配结果 / 差异列表 / 操作日志 / 导出

### 7.3 上传&解析页
- 选择sheet、表头行、数据起始行
- 预览前N行
- 校验提示：必填列是否存在（通过映射后再校验）

### 7.4 映射模板配置页（按供应商）
- 左侧：供应商列清单（来自预览）
- 中间：标准字段映射（PO、供应商物料编码、数量、含税单价、金额可选）
- 右侧：字段清洗配置（重点：物料编码清洗链）
- 下方：映射结果预览（展示：原值/清洗后/是否命中内部物料）
- 保存：生成模板版本号；任务记录使用版本

### 7.5 对账结果页
- 顶部：汇总卡片（匹配数、差异数、差异金额、未映射物料行数）
- 列表1：匹配明细（1:1、聚合可切换；聚合支持展开行）
- 列表2：差异明细（可按类型筛选：material_unmapped 等）

### 7.6 差异处理（抽屉/详情）
- 展示：供应商侧行、内部侧行（若有）、差异值、类型
- 操作：
  - 状态流转、备注、上传附件
  - 若类型=material_unmapped：提供“搜索内部物料（编码/名称/规格）→建立对照映射→保存→提示可重跑对账”

### 7.7 物料对照表管理页（采购）
- 查询：按供应商物料编码/内部物料编码/状态
- 新增/编辑/停用
- 批量导入（Excel）
- 导出对照表

### 7.8 系统配置页（管理员，可选）
- 容差参数：qty_tolerance / price_tolerance / amount_tolerance
- 留存周期：6个月（固定或可配置）

---

## 8. 字段字典（建议作为 PRD 附录A）

### 8.1 内部标准对账快照（internal_recon_snapshot_line）
| 字段 | 类型 | 必填 | 说明 |
|---|---:|---:|---|
| task_id | string | Y | 任务ID |
| po_no | string | Y | PO号 |
| internal_item_code | string | Y | 内部物料编码 |
| item_name | string | Y | 物料名称 |
| item_spec | string | Y | 规格型号 |
| grn_no | string | N | 入库单号 |
| grn_date | date | N | 入库日期 |
| qty | int | Y | 数量（整数） |
| unit_price_tax_std | decimal(18,4) | Y | 含税单价（4位） |
| calc_amount_tax | decimal(18,2/4) | Y | qty*单价（显示可2位，计算建议保留更高精度） |

### 8.2 供应商标准化行（vendor_normalized_line）
| 字段 | 类型 | 必填 | 说明 |
|---|---:|---:|---|
| task_id | string | Y | 任务ID |
| row_no | int | Y | 原Excel行号/序号 |
| po_no | string | Y | PO号 |
| supplier_item_code_raw | string | Y | 原物料编码 |
| supplier_item_code_clean | string | Y | 清洗后 |
| internal_item_code | string | N | 映射得到（未映射为空） |
| qty | int | Y | 数量（整数） |
| unit_price_tax_std | decimal(18,4) | Y | 含税单价（4位） |
| vendor_amount_tax | decimal | N | 供应商金额（如有） |
| calc_amount_tax | decimal | Y | qty*单价 |

### 8.3 差异单（recon_issue）
| 字段 | 类型 | 必填 | 说明 |
|---|---:|---:|---|
| issue_id | string | Y | 差异ID |
| task_id | string | Y | 任务ID |
| issue_type | enum | Y | material_unmapped/only_vendor/... |
| status | enum | Y | OPEN/IN_PROGRESS/RESOLVED/CLOSED |
| vendor_ref | json | N | 关联供应商行/组 |
| internal_ref | json | N | 关联内部行/组 |
| diff_qty | int | N | 数量差 |
| diff_price | decimal(18,4) | N | 单价差 |
| diff_amount | decimal | N | 金额差 |
| assignee | string | Y | 处理人（采购本人） |
| remark | string | N | 备注 |
| attachments | list | N | 附件列表 |
| created_at/updated_at | datetime | Y | 时间戳 |

---

## 9. 导出报表规范（PRD 附录B，交付给研发/测试/业务）
### 9.1 导出1：对账汇总（recon_summary.xlsx）
**Sheet：Summary**
| 列名 | 说明 |
|---|---|
| 任务ID | task_id |
| 供应商 | supplier_name |
| 期间 | period |
| 内部行数 | internal_line_count |
| 供应商行数 | vendor_line_count |
| 匹配行数 | matched_count（1:1按行，聚合按组需明确口径，建议同时给两列） |
| 匹配金额 | matched_amount |
| 差异行数 | issue_count |
| 差异金额合计 | issue_amount_sum |
| 物料未映射行数 | material_unmapped_count |
| 导出时间 | export_time |

### 9.2 导出2：匹配明细（recon_matched_detail.xlsx）
**Sheet：Matched**
| 列名 | 说明 |
|---|---|
| match_type | ONE_TO_ONE / AGGREGATE |
| PO号 | po_no |
| 内部物料编码 | internal_item_code |
| 物料名称 | item_name |
| 规格型号 | item_spec |
| 含税单价(4位) | unit_price_tax_std |
| 供应商数量 | vendor_qty（聚合则为sum） |
| 内部数量 | internal_qty（聚合则为sum） |
| 供应商计算金额 | vendor_calc_amount |
| 内部计算金额 | internal_calc_amount |
| 供应商行引用 | 如 “row 5,7,9” 或 group_id |
| 内部行引用 | 如 “grn xxx 行1,2” 或 group_id |

### 9.3 导出3：差异明细（recon_issue_detail.xlsx）
**Sheet：Issues**
| 列名 | 说明 |
|---|---|
| issue_id | 差异ID |
| issue_type | 差异类型 |
| status | 状态 |
| PO号 | po_no（若可提取） |
| 内部物料编码 | internal_item_code（若有） |
| 供应商物料编码(原) | supplier_item_code_raw |
| 供应商物料编码(清洗后) | supplier_item_code_clean |
| 内部物料名称 | item_name（若有） |
| 规格型号 | item_spec（若有） |
| 供应商数量 | vendor_qty |
| 内部数量 | internal_qty |
| 数量差 | diff_qty |
| 供应商含税单价 | vendor_price |
| 内部含税单价 | internal_price |
| 单价差 | diff_price |
| 金额差 | diff_amount |
| 处理人 | assignee |
| 备注 | remark |
| 最后更新时间 | updated_at |

### 9.4 证据包（可选）
- 原始供应商Excel（原文件）
- 解析后的标准化数据导出（可选）
- 上述三类报表

---

## 10. 接口草案（PRD 附录C）
> 以下为 REST 风格草案；字段名可按你们后端规范调整（snake/camel均可）。

### 10.1 任务
**POST /api/recon/tasks**
- 入参：supplier_id, period_start, period_end, remark
- 出参：task_id, status

**GET /api/recon/tasks**
- 入参：supplier_id?, status?, period?
- 出参：list(tasks)

**GET /api/recon/tasks/{task_id}**
- 出参：任务详情、内部快照统计、文件信息、模板版本、结果统计

**POST /api/recon/tasks/{task_id}/void**
- 入参：reason
- 出参：status=VOID

**POST /api/recon/tasks/{task_id}/close**
- 出参：status=CLOSED

### 10.2 上传与解析
**POST /api/recon/tasks/{task_id}/vendor-file**
- 入参：file（xlsx）, sheet_name?, header_row?, data_start_row?
- 出参：file_id, parse_status

**GET /api/recon/tasks/{task_id}/vendor-file/preview**
- 入参：rows=50
- 出参：columns, preview_rows

### 10.3 模板（按供应商）
**GET /api/recon/suppliers/{supplier_id}/templates**
- 出参：模板列表（含版本）

**POST /api/recon/suppliers/{supplier_id}/templates**
- 入参：
  - template_name
  - column_mapping: {standard_field: vendor_column}
  - cleaning_config: { item_code: [ops...] }
  - enable_item_mapping: true
- 出参：template_id, version

**POST /api/recon/tasks/{task_id}/apply-template**
- 入参：template_id, version
- 出参：task.status=MAPPING_READY

### 10.4 对照表（采购维护）
**GET /api/recon/suppliers/{supplier_id}/item-mappings**
- 入参：keyword?, status?
- 出参：list

**POST /api/recon/suppliers/{supplier_id}/item-mappings**
- 入参：supplier_item_code_raw?, supplier_item_code_clean?, internal_item_code
- 出参：mapping_id

**POST /api/recon/suppliers/{supplier_id}/item-mappings/import**
- 入参：file(xlsx)
- 出参：success_count, fail_rows（含原因）

**PATCH /api/recon/suppliers/{supplier_id}/item-mappings/{mapping_id}**
- 入参：status/ internal_item_code / remark
- 出参：updated

### 10.5 执行对账
**POST /api/recon/tasks/{task_id}/reconcile**
- 入参：force_rerun:boolean（重跑）
- 出参：job_id, status=RECONCILING

**GET /api/recon/tasks/{task_id}/reconcile-result**
- 出参：summary + matched_list（分页） + issue_list（分页）

### 10.6 差异处理
**PATCH /api/recon/issues/{issue_id}**
- 入参：status?, remark?, assignee?
- 出参：issue

**POST /api/recon/issues/{issue_id}/attachments**
- 入参：file
- 出参：attachment_id, url

**POST /api/recon/issues/{issue_id}/create-item-mapping**
- 入参：internal_item_code（从内部物料搜索选择）
- 出参：mapping_id（创建成功后提示可重跑）

### 10.7 导出
**POST /api/recon/tasks/{task_id}/export**
- 入参：export_type = summary/matched/issues/evidence_pack
- 出参：download_url（异步生成可返回 job_id）

---

## 11. 测试验收用例（PRD 附录D，最小集合）
1) 数量为 `10.0` 能转为 10；数量为 `10.5` → data_invalid  
2) 单价统一 round(4) 后参与匹配与导出展示一致  
3) 物料编码清洗（去前缀/去分隔符/大小写）后可命中内部编码  
4) 对照表优先级高于“清洗后直连内部编码”的等值命中  
5) 1:1 匹配成功；聚合匹配（供应商1行↔内部2行）成功且可展开显示关联行  
6) material_unmapped 在差异页创建映射后重跑，对应行进入匹配  
7) 采购A不可见采购B的任务/对照表（权限隔离）  
8) 导出三类报表字段齐全、数据与页面一致

---

## 12. 待业务确认项
- price_tolerance 默认值（建议 0.0001）
- amount_tolerance 默认值（建议 0.01）
- 匹配统计口径：聚合匹配“匹配行数”按“组”还是按“内部行+供应商行”分别统计（建议：同时给 matched_group_count、matched_line_count）

---

