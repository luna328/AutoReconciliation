# MySQL Learning-First Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build database integration while prioritizing MySQL learning outcomes (SQL fluency, schema design, indexing, transactions, debugging) over pure delivery speed.

**Architecture:** Start from raw MySQL operations and SQL scripts, then gradually map them into Flask APIs and finally ORM usage. Keep each stage independently verifiable so you can understand what the database is doing before hiding details behind framework abstractions.

**Tech Stack:** MySQL 8, Flask, SQLAlchemy, Flask-Migrate, PyMySQL, unittest, mysql client

---

## 0. 与“功能交付导向计划”的区别

- 本计划（学习导向）先训练 SQL 与数据库思维，再做业务接线，目标是“你会 MySQL”。
- 之前计划（功能导向，`docs/plans/2026-03-04-mysql-mvp-persistence.md`）优先快速落地可用功能，目标是“系统先跑起来”。
- 本计划会额外增加：手写 SQL、Explain 分析、事务实验、索引实验、故障演练、学习笔记产出。
- 本计划允许阶段性“代码尚未完全业务可用”，但每个阶段都必须有明确学习成果和验证证据。

---

### Task 1: 搭建本地 MySQL 学习实验环境

**Files:**
- Create: `docs/learning/mysql-learning-checklist.md`
- Create: `.env.example`
- Test: `tests/test_mysql_env.py`

**Step 1: Write the failing test**

Create `tests/test_mysql_env.py`:

```python
import os
import unittest


class TestMySqlEnv(unittest.TestCase):
    def test_database_url_declared(self):
        self.assertTrue("DATABASE_URL" in os.environ or os.path.exists(".env"))
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_mysql_env.py -v`
Expected: FAIL (环境变量或 `.env` 未准备)

**Step 3: Write minimal implementation**

- 在 `.env.example` 写入本地连接串示例。
- 在 `docs/learning/mysql-learning-checklist.md` 记录：安装 MySQL、创建用户、授权、连接测试命令。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_mysql_env.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add .env.example docs/learning/mysql-learning-checklist.md tests/test_mysql_env.py
git commit -m "docs: 初始化MySQL学习环境清单"
```

### Task 2: 先用纯 SQL 建表（不借助 ORM）

**Files:**
- Create: `docs/learning/sql/01_create_schema.sql`
- Create: `docs/learning/sql/02_seed_demo_data.sql`
- Test: `tests/test_schema_sql_files.py`

**Step 1: Write the failing test**

Create `tests/test_schema_sql_files.py`:

```python
import os
import unittest


class TestSchemaSqlFiles(unittest.TestCase):
    def test_sql_files_exist(self):
        self.assertTrue(os.path.exists("docs/learning/sql/01_create_schema.sql"))
        self.assertTrue(os.path.exists("docs/learning/sql/02_seed_demo_data.sql"))
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_schema_sql_files.py -v`
Expected: FAIL (SQL 文件未创建)

**Step 3: Write minimal implementation**

- 在 `01_create_schema.sql` 手写 3 张表：
  - `reconcile_task`
  - `upload_record`
  - `reconcile_result`
- 在 `02_seed_demo_data.sql` 插入 2~3 条示例数据。
- 要求显式写主键、外键、唯一约束、时间字段默认值。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_schema_sql_files.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/learning/sql/01_create_schema.sql docs/learning/sql/02_seed_demo_data.sql tests/test_schema_sql_files.py
git commit -m "feat: 增加MySQL手写建表与示例数据脚本"
```

### Task 3: SQL 基础 CRUD 训练（先命令行）

**Files:**
- Create: `docs/learning/sql/03_crud_practice.sql`
- Create: `docs/learning/sql/04_join_and_group_practice.sql`
- Create: `docs/learning/mysql-crud-notes.md`
- Test: `tests/test_sql_practice_docs.py`

**Step 1: Write the failing test**

Create `tests/test_sql_practice_docs.py`:

```python
import os
import unittest


class TestSqlPracticeDocs(unittest.TestCase):
    def test_learning_notes_exist(self):
        self.assertTrue(os.path.exists("docs/learning/mysql-crud-notes.md"))
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_sql_practice_docs.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 编写 `03_crud_practice.sql`：INSERT/SELECT/UPDATE/DELETE。
- 编写 `04_join_and_group_practice.sql`：JOIN、GROUP BY、HAVING、ORDER BY。
- 在 `mysql-crud-notes.md` 记录每条 SQL 的目标、结果、易错点。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_sql_practice_docs.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/learning/sql/03_crud_practice.sql docs/learning/sql/04_join_and_group_practice.sql docs/learning/mysql-crud-notes.md tests/test_sql_practice_docs.py
git commit -m "docs: 补充SQL基础CRUD与聚合练习"
```

### Task 4: 索引与执行计划学习（EXPLAIN）

**Files:**
- Create: `docs/learning/sql/05_index_experiment.sql`
- Create: `docs/learning/mysql-explain-notes.md`
- Test: `tests/test_index_learning_assets.py`

**Step 1: Write the failing test**

Create `tests/test_index_learning_assets.py`:

```python
import os
import unittest


class TestIndexLearningAssets(unittest.TestCase):
    def test_explain_notes_exist(self):
        self.assertTrue(os.path.exists("docs/learning/mysql-explain-notes.md"))
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_index_learning_assets.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 在 `05_index_experiment.sql` 写：
  - 无索引查询
  - 创建联合索引 `(task_id, file_type)`
  - 再次 EXPLAIN 对比
- 在 `mysql-explain-notes.md` 记录 `type/key/rows/extra` 的变化与结论。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_index_learning_assets.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/learning/sql/05_index_experiment.sql docs/learning/mysql-explain-notes.md tests/test_index_learning_assets.py
git commit -m "docs: 增加索引与EXPLAIN学习实验"
```

### Task 5: 事务与回滚实验

**Files:**
- Create: `docs/learning/sql/06_transaction_lab.sql`
- Create: `docs/learning/mysql-transaction-notes.md`
- Test: `tests/test_transaction_learning_assets.py`

**Step 1: Write the failing test**

Create `tests/test_transaction_learning_assets.py`:

```python
import os
import unittest


class TestTransactionLearningAssets(unittest.TestCase):
    def test_transaction_lab_exists(self):
        self.assertTrue(os.path.exists("docs/learning/sql/06_transaction_lab.sql"))
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_transaction_learning_assets.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 在 `06_transaction_lab.sql` 编写：
  - `START TRANSACTION`
  - 插入任务 + 上传记录
  - 模拟异常后 `ROLLBACK`
  - 对比 `COMMIT` 后结果
- 在 `mysql-transaction-notes.md` 记录“原子性”在本项目中的意义。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_transaction_learning_assets.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/learning/sql/06_transaction_lab.sql docs/learning/mysql-transaction-notes.md tests/test_transaction_learning_assets.py
git commit -m "docs: 增加事务与回滚实验"
```

### Task 6: 用最小 Python 脚本直连 MySQL（不走 Flask）

**Files:**
- Create: `scripts/mysql_learning_lab.py`
- Test: `tests/test_mysql_learning_script.py`

**Step 1: Write the failing test**

Create `tests/test_mysql_learning_script.py`:

```python
import os
import unittest


class TestMySqlLearningScript(unittest.TestCase):
    def test_script_exists(self):
        self.assertTrue(os.path.exists("scripts/mysql_learning_lab.py"))
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_mysql_learning_script.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

在 `scripts/mysql_learning_lab.py` 实现：
- 读取 `DATABASE_URL`
- 执行 3 个 SQL：创建任务、查询任务、更新状态
- 打印执行结果（行数、任务ID）

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_mysql_learning_script.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/mysql_learning_lab.py tests/test_mysql_learning_script.py
git commit -m "feat: 增加Python直连MySQL学习脚本"
```

### Task 7: 将学习结果映射到 Flask（先任务接口）

**Files:**
- Modify: `app.py`
- Create: `extensions.py`
- Create: `models.py`
- Test: `tests/test_task_api.py`

**Step 1: Write the failing test**

Create `tests/test_task_api.py`:

```python
import unittest

from app import app


class TestTaskApi(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_create_task_returns_task_id(self):
        resp = self.client.post("/api/task/create", json={})
        self.assertEqual(resp.status_code, 200)
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_task_api.py -v`
Expected: FAIL (接口未实现)

**Step 3: Write minimal implementation**

- 接入 SQLAlchemy 和模型。
- 仅实现 `POST /api/task/create` + `GET /api/task/<task_id>`。
- 确保你能在数据库里看到新增任务行。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_task_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app.py extensions.py models.py tests/test_task_api.py
git commit -m "feat: 接入Flask任务接口并落库"
```

### Task 8: 完成上传/对账/导出的 task_id 数据闭环

**Files:**
- Modify: `app.py`
- Modify: `static/js/app.js`
- Modify: `templates/index.html`
- Test: `tests/test_upload_api_with_task.py`
- Test: `tests/test_reconcile_api_with_task.py`
- Test: `tests/test_export_api_with_task.py`

**Step 1: Write the failing test**

分别写 3 个测试，要求：
- 上传必须带 `task_id`
- 对账必须带 `task_id`
- 导出必须带 `task_id`

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_upload_api_with_task.py tests/test_reconcile_api_with_task.py tests/test_export_api_with_task.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 后端改造：按 `task_id` 查询/写入 DB。
- 前端改造：统一传递 `task_id`。
- 保持对账核心算法不变。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_upload_api_with_task.py tests/test_reconcile_api_with_task.py tests/test_export_api_with_task.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app.py static/js/app.js templates/index.html tests/test_upload_api_with_task.py tests/test_reconcile_api_with_task.py tests/test_export_api_with_task.py
git commit -m "feat: 完成task_id全链路持久化闭环"
```

### Task 9: 学习成果复盘与能力验收

**Files:**
- Create: `docs/learning/mysql-learning-retrospective.md`
- Modify: `project.md`
- Modify: `README_使用说明.txt`

**Step 1: Write the failing test/checklist**

在 `mysql-learning-retrospective.md` 建立能力清单并自测：

1. 我能手写建表 SQL 并解释约束含义。
2. 我能用 EXPLAIN 判断索引是否生效。
3. 我能解释事务回滚如何保护任务一致性。
4. 我能定位常见连接错误（权限、端口、库不存在）。
5. 我能讲清楚 ORM 与原生 SQL 的取舍。

**Step 2: Run verification before finalization**

Run: `python -m unittest -v`
Expected: PASS

**Step 3: Write minimal implementation**

- 在 `project.md` 增加“学习目标达成情况”章节。
- 在 `README_使用说明.txt` 增加“学习路径：先 SQL 后 ORM”的说明。
- 完成复盘文档，附至少 3 个你真实踩坑与解决方法。

**Step 4: Re-run verification**

Run: `python -m unittest -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/learning/mysql-learning-retrospective.md project.md README_使用说明.txt
git commit -m "docs: 完成MySQL学习导向方案复盘与验收"
```

---

## 学习导向计划的验收标准（与功能导向不同）

- 你能脱离 ORM，直接用 SQL 完成建表、查询、事务控制。
- 你能解释并验证索引效果，不只会“加索引”。
- 你能独立定位 3 类常见 MySQL 问题（连接、SQL 语法、约束冲突）。
- 你不仅完成功能，还形成可复用学习文档与实验脚本。
