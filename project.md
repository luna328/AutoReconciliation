# 自动对账系统数据库改造需求（本地 MySQL MVP）

## 1. 背景
- 当前系统基于 Flask + Pandas，核心状态使用 `current_task` 保存在进程内存。
- 现状问题：服务重启后任务与结果丢失；无法稳定支持多任务并行；历史结果不可追溯。
- 本次目标：先在本地完成 MySQL 接入与业务打通，后续再考虑云端数据库部署。

## 2. 本次改造目标
- 将任务、上传记录、对账结果从内存迁移到数据库持久化。
- 对账链路全程以 `task_id` 作为唯一标识。
- 保持现有对账算法和页面主体不变，优先完成最小可用（MVP）。

## 3. 范围

### 3.1 In Scope（本次必须完成）
- 本地 MySQL 连接配置与连通性验证。
- ORM 模型与迁移机制接入（建议 SQLAlchemy + Flask-Migrate）。
- 新增任务主表、上传记录表、结果表。
- 现有接口改造为按 `task_id` 读写。
- 前端保存当前 `task_id`，并可按 `task_id` 回查结果。

### 3.2 Out of Scope（本次不做）
- 用户体系与权限控制。
- 服务器部署、读写分离、备份容灾。
- 消息队列、异步任务系统、复杂报表分析。

## 4. 功能需求

### 4.1 任务创建
- 系统支持创建对账任务，返回 `task_id`。
- 任务初始状态为 `created`。

### 4.2 文件上传持久化
- 供应商文件、系统入库文件上传后：
  - 文件仍保存到 `uploads/` 目录；
  - 同步写入数据库上传记录（原文件名、保存路径、行数、列信息、预览数据）。
- 当两侧文件都上传完成后，任务状态更新为 `uploaded`。

### 4.3 对账执行持久化
- 对账请求必须携带 `task_id`。
- 后端从数据库读取任务关联上传数据，执行现有对账逻辑。
- 对账完成后写入 `reconcile_result`（汇总、明细 JSON，映射参数，容差参数）。
- 任务状态更新为 `reconciled`；失败时更新为 `failed` 并记录错误信息。

### 4.4 导出按任务读取
- 导出接口必须按 `task_id` 读取结果，不再依赖内存变量。
- 支持历史任务重复导出。

### 4.5 历史查询
- 支持按 `task_id` 查看任务状态、上传概览、对账汇总。
- 支持查询最近任务列表（MVP 可限制最近 N 条）。

## 5. 数据模型（MVP）

### 5.1 `reconcile_task`
- `id` (PK, string/uuid)
- `status` (created/uploaded/reconciled/failed)
- `created_at`
- `updated_at`

### 5.2 `upload_record`
- `id` (PK)
- `task_id` (FK -> reconcile_task.id)
- `file_type` (vendor/internal)
- `original_name`
- `saved_path`
- `row_count`
- `columns_json`
- `preview_json`
- `created_at`

### 5.3 `reconcile_result`
- `id` (PK)
- `task_id` (FK -> reconcile_task.id, unique)
- `summary_json`
- `result_json`
- `mapping_json`
- `tolerance_json`
- `created_at`
- `updated_at`

## 6. 接口改造需求

### 6.1 新增接口
- `POST /api/task/create`：创建任务并返回 `task_id`。
- `GET /api/task/<task_id>`：获取任务详情（状态、上传信息、结果摘要）。
- `GET /api/tasks/recent`：获取最近任务列表。

### 6.2 改造接口
- `POST /api/upload/vendor`：新增 `task_id` 入参。
- `POST /api/upload/internal`：新增 `task_id` 入参。
- `POST /api/reconcile`：必须携带 `task_id`。
- `POST /api/export`：必须携带 `task_id`。

## 7. 前端展示与交互需求
- 页面展示“当前任务ID + 任务状态”。
- 上传、对账、导出请求统一携带 `task_id`。
- 对账结果区展示“任务时间、容差参数、映射配置摘要”。
- 新增“最近任务”入口，支持点击回看历史任务结果。

## 8. 非功能需求
- 配置安全：数据库连接信息通过环境变量提供，不写死在代码。
- 可追踪性：关键日志打印 `task_id`。
- 兼容性：保持现有 Excel 上传/预览/导出行为一致。
- 性能目标：MVP 以正确性优先，单次对账响应时延不劣化明显。

## 9. 验收标准（Done Definition）
- 服务重启后，已完成任务结果可按 `task_id` 查询。
- 同时创建多个任务时，数据互不覆盖。
- 导出结果可基于历史任务重复下载。
- 页面汇总与导出数据一致。
- 发生异常时可通过日志中的 `task_id` 快速定位。

## 10. 实施顺序建议
1. 建库与连接验证。
2. 建模与迁移落表。
3. 创建任务接口与前端 `task_id` 状态。
4. 上传链路写库。
5. 对账链路写库。
6. 导出改造为按任务读取。
7. 历史查询与前端展示。
8. 回归测试与缺陷修复。

## 11. 风险与应对
- 风险：接口一次性改动过大导致前端联调失败。
  - 应对：分阶段改造，优先保留旧逻辑兜底，再逐步切换。
- 风险：结果 JSON 过大导致查询缓慢。
  - 应对：先保留全量 JSON，后续可增加摘要字段与分页查询。
- 风险：本地 MySQL 环境差异导致连通问题。
  - 应对：提供统一 `.env.example` 与初始化 SQL/迁移命令。
