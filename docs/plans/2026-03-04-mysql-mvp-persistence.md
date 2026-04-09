# 本地 MySQL 持久化 MVP 实施计划

> **给 Claude：** 必须使用子技能 `superpowers:executing-plans` 按任务逐项执行本计划。

**目标：** 将当前基于内存的 `current_task` 状态改为本地 MySQL 持久化，使任务在服务重启后仍可按 `task_id` 查询、复查与导出。

**架构：** 保持 `app.py` 内现有 Excel 解析和对账算法不变，新增 SQLAlchemy 数据层（`models.py`），并通过 Flask-Migrate 管理表结构。上传文件仍存放在 `uploads/`，数据库仅保存任务、上传元数据、对账结果 JSON 和任务状态。

**技术栈：** Flask、SQLAlchemy、Flask-Migrate、PyMySQL、pandas、unittest（Flask test client）

---

### 任务 1：补齐依赖并初始化数据库配置

**涉及文件：**
- 修改：`requirements.txt`
- 修改：`app.py`
- 新增：`.env.example`

**步骤 1：先写失败测试**

新建 `tests/test_config_db.py`：

```python
import os
import unittest


class TestDbConfig(unittest.TestCase):
    def test_database_url_env_exists_or_has_default(self):
        value = os.getenv("DATABASE_URL", "")
        self.assertTrue(isinstance(value, str))
```

**步骤 2：运行测试确认先失败**

执行：`python -m unittest tests/test_config_db.py -v`

预期：失败（`tests` 尚未建立或配置尚未接线）

**步骤 3：写最小实现**

- 在 `requirements.txt` 增加依赖：
  - `sqlalchemy>=2.0.0`
  - `flask-sqlalchemy>=3.1.0`
  - `flask-migrate>=4.0.0`
  - `pymysql>=1.1.0`
  - `python-dotenv>=1.0.0`
- 在 `app.py` 中通过 `dotenv` 读取环境变量，并设置：
  - `SQLALCHEMY_DATABASE_URI` <- `DATABASE_URL`
  - `SQLALCHEMY_TRACK_MODIFICATIONS = False`
- 新建 `.env.example`，写入本地 MySQL 连接示例。

**步骤 4：再次运行测试确认通过**

执行：`python -m unittest tests/test_config_db.py -v`

预期：通过

**步骤 5：提交**

```bash
git add requirements.txt app.py .env.example tests/test_config_db.py
git commit -m "chore: 补齐MySQL依赖与基础配置"
```

### 任务 2：引入 DB 扩展并创建核心模型

**涉及文件：**
- 新增：`extensions.py`
- 新增：`models.py`
- 修改：`app.py`
- 测试：`tests/test_models_schema.py`

**步骤 1：先写失败测试**

新建 `tests/test_models_schema.py`：

```python
import unittest

from app import app
from extensions import db
from models import ReconcileTask, UploadRecord, ReconcileResult


class TestModelSchema(unittest.TestCase):
    def test_model_tables_exist(self):
        self.assertEqual(ReconcileTask.__tablename__, "reconcile_task")
        self.assertEqual(UploadRecord.__tablename__, "upload_record")
        self.assertEqual(ReconcileResult.__tablename__, "reconcile_result")

    def test_relationships_declared(self):
        self.assertTrue(hasattr(ReconcileTask, "uploads"))
        self.assertTrue(hasattr(ReconcileTask, "result"))
```

**步骤 2：运行测试确认先失败**

执行：`python -m unittest tests/test_models_schema.py -v`

预期：失败（`extensions` / `models` 未创建）

**步骤 3：写最小实现**

- `extensions.py`：定义 `db = SQLAlchemy()`、`migrate = Migrate()`。
- `models.py`：定义三张核心表：
  - `ReconcileTask(id, status, created_at, updated_at, error_message)`
  - `UploadRecord(id, task_id, file_type, original_name, saved_path, row_count, columns_json, preview_json, created_at)`
  - `ReconcileResult(id, task_id(unique), summary_json, result_json, mapping_json, tolerance_json, created_at, updated_at)`
- 关系：
  - `ReconcileTask.uploads` 一对多
  - `ReconcileTask.result` 一对一
- 在 `app.py` 初始化处接入 `db.init_app(app)` 和 `migrate.init_app(app, db)`。

**步骤 4：再次运行测试确认通过**

执行：`python -m unittest tests/test_models_schema.py -v`

预期：通过

**步骤 5：提交**

```bash
git add extensions.py models.py app.py tests/test_models_schema.py
git commit -m "feat: 新增持久化模型与数据库扩展"
```

### 任务 3：建立迁移流程并生成初始表结构

**涉及文件：**
- 新增：`migrations/`（自动生成）
- 修改：`README_使用说明.txt`
- 测试：`tests/test_db_bootstrap.py`

**步骤 1：先写失败测试**

新建 `tests/test_db_bootstrap.py`：

```python
import os
import unittest


class TestDbBootstrap(unittest.TestCase):
    def test_migration_folder_exists(self):
        self.assertTrue(os.path.isdir("migrations"))
```

**步骤 2：运行测试确认先失败**

执行：`python -m unittest tests/test_db_bootstrap.py -v`

预期：失败（`migrations` 目录不存在）

**步骤 3：写最小实现**

顺序执行：

```bash
flask db init
flask db migrate -m "init reconciliation persistence tables"
flask db upgrade
```

更新 `README_使用说明.txt` 的本地启动说明：
- `pip install -r requirements.txt`
- `flask db upgrade`
- `python app.py`

**步骤 4：再次运行测试确认通过**

执行：`python -m unittest tests/test_db_bootstrap.py -v`

预期：通过

**步骤 5：提交**

```bash
git add migrations README_使用说明.txt tests/test_db_bootstrap.py
git commit -m "chore: 建立迁移流程并落地初始表结构"
```

### 任务 4：实现任务生命周期接口

**涉及文件：**
- 修改：`app.py`
- 测试：`tests/test_task_api.py`

**步骤 1：先写失败测试**

新建 `tests/test_task_api.py`：

```python
import unittest

from app import app


class TestTaskApi(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_create_task_returns_task_id(self):
        resp = self.client.post("/api/task/create", json={})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        self.assertTrue(data["task_id"])
```

**步骤 2：运行测试确认先失败**

执行：`python -m unittest tests/test_task_api.py -v`

预期：失败（接口不存在，404）

**步骤 3：写最小实现**

在 `app.py` 新增：

- `POST /api/task/create`
  - 创建 `ReconcileTask`，状态 `created`
  - 返回 `{ success: true, task_id }`
- `GET /api/task/<task_id>`
  - 返回任务状态、上传摘要、结果摘要（如有）
- `GET /api/tasks/recent`
  - 返回最近任务列表（按创建时间倒序，默认 limit=20）

**步骤 4：再次运行测试确认通过**

执行：`python -m unittest tests/test_task_api.py -v`

预期：通过

**步骤 5：提交**

```bash
git add app.py tests/test_task_api.py
git commit -m "feat: 新增任务创建与查询接口"
```

### 任务 5：改造上传接口为 task_id 持久化

**涉及文件：**
- 修改：`app.py`
- 测试：`tests/test_upload_api_with_task.py`

**步骤 1：先写失败测试**

新建 `tests/test_upload_api_with_task.py`：

```python
import io
import unittest

from app import app


class TestUploadApiWithTask(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_upload_vendor_requires_task_id(self):
        data = {"file": (io.BytesIO(b"x"), "a.xlsx")}
        resp = self.client.post("/api/upload/vendor", data=data, content_type="multipart/form-data")
        body = resp.get_json()
        self.assertFalse(body["success"])
```

**步骤 2：运行测试确认先失败**

执行：`python -m unittest tests/test_upload_api_with_task.py -v`

预期：失败（当前接口未强制 `task_id`）

**步骤 3：写最小实现**

修改 `app.py` 中 `/api/upload/vendor`、`/api/upload/internal`：

- 强制读取 `task_id`（FormData）
- 校验 `task_id` 对应任务存在
- 保留现有解析与预览逻辑
- 用数据库替代 `current_task`：
  - 以 `task_id + file_type` 维度 upsert `UploadRecord`
- 若 vendor/internal 均上传完成，任务状态更新为 `uploaded`

**步骤 4：再次运行测试确认通过**

执行：`python -m unittest tests/test_upload_api_with_task.py -v`

预期：通过

**步骤 5：提交**

```bash
git add app.py tests/test_upload_api_with_task.py
git commit -m "feat: 上传链路改为按task_id持久化"
```

### 任务 6：改造对账接口为 DB 读写

**涉及文件：**
- 修改：`app.py`
- 测试：`tests/test_reconcile_api_with_task.py`

**步骤 1：先写失败测试**

新建 `tests/test_reconcile_api_with_task.py`：

```python
import unittest

from app import app


class TestReconcileApiWithTask(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_reconcile_requires_task_id(self):
        resp = self.client.post("/api/reconcile", json={})
        body = resp.get_json()
        self.assertFalse(body["success"])
```

**步骤 2：运行测试确认先失败**

执行：`python -m unittest tests/test_reconcile_api_with_task.py -v`

预期：失败（当前仍依赖 `current_task`）

**步骤 3：写最小实现**

修改 `/api/reconcile`：

- 强制读取 `task_id`
- 按 `task_id` 查询 vendor/internal 的 `UploadRecord`
- 从 `saved_path` 读回 DataFrame（复用已有解析逻辑）
- 调用现有 `perform_reconciliation(...)`
- upsert `ReconcileResult`
- 成功状态写 `reconciled`
- 异常状态写 `failed`，并记录 `error_message`

**步骤 4：再次运行测试确认通过**

执行：`python -m unittest tests/test_reconcile_api_with_task.py -v`

预期：通过

**步骤 5：提交**

```bash
git add app.py tests/test_reconcile_api_with_task.py
git commit -m "feat: 对账结果按task_id持久化并记录状态"
```

### 任务 7：改造导出接口为按 task_id 查询

**涉及文件：**
- 修改：`app.py`
- 测试：`tests/test_export_api_with_task.py`

**步骤 1：先写失败测试**

新建 `tests/test_export_api_with_task.py`：

```python
import unittest

from app import app


class TestExportApiWithTask(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_export_requires_task_id(self):
        resp = self.client.post("/api/export", json={})
        data = resp.get_json()
        self.assertFalse(data["success"])
```

**步骤 2：运行测试确认先失败**

执行：`python -m unittest tests/test_export_api_with_task.py -v`

预期：失败（当前导出来自内存 `current_task`）

**步骤 3：写最小实现**

修改 `/api/export`：

- 强制读取 `task_id`
- 按 `task_id` 查询 `ReconcileResult`
- 从 `result_json` 组装 Excel（复用现有 sheet 规则）
- 若任务无结果，返回可读错误 JSON

**步骤 4：再次运行测试确认通过**

执行：`python -m unittest tests/test_export_api_with_task.py -v`

预期：通过

**步骤 5：提交**

```bash
git add app.py tests/test_export_api_with_task.py
git commit -m "feat: 导出接口支持按task_id历史导出"
```

### 任务 8：前端接入 task_id 并增加最近任务展示

**涉及文件：**
- 修改：`templates/index.html`
- 修改：`static/js/app.js`
- 修改：`static/css/style.css`
- 测试：浏览器手工验证

**步骤 1：先写失败验证清单**

手工验证项：

1. 首页可见“当前任务ID/状态”区域。
2. 未创建任务时，不允许上传流程继续。
3. 上传/对账/导出请求都携带 `task_id`。
4. 页面刷新后可拉取最近任务并回看。

**步骤 2：先运行并确认当前行为不满足**

执行：`python app.py`，浏览器访问页面。

预期：不满足（当前无任务概念）

**步骤 3：写最小实现**

- `index.html` 新增：
  - 当前任务信息卡（`task_id`、状态）
  - 最近任务列表容器
- `app.js`：
  - 新增 `currentTaskId` 状态
  - 页面加载调用 `POST /api/task/create`
  - 上传 FormData 增加 `task_id`
  - 对账/导出 JSON 带上 `task_id`
  - 新增 `loadRecentTasks()`，支持点击任务回看详情
- `style.css`：补充对应样式，保持现有视觉主风格。

**步骤 4：再次验证确认通过**

执行：`python app.py`，按清单逐项验证。

预期：全部通过

**步骤 5：提交**

```bash
git add templates/index.html static/js/app.js static/css/style.css
git commit -m "feat: 前端接入task_id流程并展示最近任务"
```

### 任务 9：收尾验证与文档补齐

**涉及文件：**
- 修改：`project.md`
- 修改：`README_使用说明.txt`
- 新增：`docs/learning/本地MySQL接入与验证清单.md`

**步骤 1：先写验收清单文档**

在 `docs/learning/本地MySQL接入与验证清单.md` 写入 5 条验收标准：

1. 重启服务后，历史任务可查询。
2. 多个 `task_id` 互不覆盖。
3. 历史任务可重复导出。
4. 页面汇总与导出结果一致。
5. 失败任务包含 `error_message` 可排查。

**步骤 2：运行全量测试**

执行：`python -m unittest -v`

预期：全部通过

**步骤 3：补齐文档实现细节**

- `project.md`：同步实际落地接口和字段（如与计划存在差异，以代码为准更新）。
- `README_使用说明.txt`：补充
  - 本地 MySQL 准备步骤
  - `.env` 配置
  - 迁移命令与启动命令
  - 常见错误排查

**步骤 4：再次回归验证**

执行：`python -m unittest -v`

预期：全部通过

**步骤 5：提交**

```bash
git add project.md README_使用说明.txt docs/learning/本地MySQL接入与验证清单.md
git commit -m "docs: 补充本地MySQL接入说明与验收清单"
```

---

## 执行注意事项

- 每个后端改造步骤都遵守 `@test-driven-development`：先测再改。
- 在声称“完成”前执行 `@verification-before-completion`。
- 能不改动核心对账算法就不改，优先做状态与存储层改造。
- 接口协议以 `task_id` 为主，不建议继续依赖 `current_task`。
