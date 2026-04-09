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

**本任务目的：**
- 建立可复用的数据库配置契约（`.env.example` + `DATABASE_URL` 约定）。
- 降低环境差异导致的学习阻塞，确保后续 SQL/脚本/API 任务都有统一入口。
- 用最小测试把“环境准备完成”从口头约定变成可执行验证。

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

**本任务目的：**
- 先掌握数据库第一性原理：手写 Schema，而不是先依赖 ORM 抽象。
- 用行为测试验证关键约束（外键、唯一约束、级联删除）真实生效。
- 为后续 CRUD、事务、Flask API 打下稳定的数据结构与一致性基础。

**Files:**
- Create: `docs/learning/sql/01_create_schema.sql`
- Create: `docs/learning/sql/02_seed_demo_data.sql`
- Create: `tests/test_schema_constraints.py`

**Step 1: Write the failing test（L1/L2：结构+约束行为）**

Create `tests/test_schema_constraints.py`（核心断言）：

```python
import unittest
import pymysql


class TestSchemaConstraints(unittest.TestCase):
    def setUp(self):
        self.conn = pymysql.connect(host="127.0.0.1", user="recon_user", password="recon_pass", database="reconciliation", autocommit=True)
        self.cur = self.conn.cursor()

    def tearDown(self):
        self.cur.close()
        self.conn.close()

    def test_upload_record_requires_existing_task(self):
        with self.assertRaises(pymysql.err.IntegrityError):
            self.cur.execute("INSERT INTO upload_record(task_id, file_type, file_name) VALUES (999999, 'left', 'x.csv')")

    def test_reconcile_result_task_id_is_unique(self):
        self.cur.execute("INSERT INTO reconcile_task(task_name, status) VALUES ('uq-test', 'created')")
        self.cur.execute("SELECT LAST_INSERT_ID()")
        task_id = self.cur.fetchone()[0]
        self.cur.execute("INSERT INTO reconcile_result(task_id, result_status, diff_count) VALUES (%s, 'done', 0)", (task_id,))
        with self.assertRaises(pymysql.err.IntegrityError):
            self.cur.execute("INSERT INTO reconcile_result(task_id, result_status, diff_count) VALUES (%s, 'done', 1)", (task_id,))

    def test_delete_task_cascades_children(self):
        self.cur.execute("INSERT INTO reconcile_task(task_name, status) VALUES ('cascade-test', 'created')")
        self.cur.execute("SELECT LAST_INSERT_ID()")
        task_id = self.cur.fetchone()[0]
        self.cur.execute("INSERT INTO upload_record(task_id, file_type, file_name) VALUES (%s, 'left', 'a.csv')", (task_id,))
        self.cur.execute("DELETE FROM reconcile_task WHERE id=%s", (task_id,))
        self.cur.execute("SELECT COUNT(*) FROM upload_record WHERE task_id=%s", (task_id,))
        self.assertEqual(self.cur.fetchone()[0], 0)
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_schema_constraints.py -v`
Expected: FAIL（建表未完成或约束不正确时失败）

**Step 3: Write minimal implementation**

- 在 `01_create_schema.sql` 手写 3 张表：`reconcile_task`、`upload_record`、`reconcile_result`。
- 显式写主键、外键、`reconcile_result.task_id` 唯一约束、时间字段默认值。
- 在 `02_seed_demo_data.sql` 写入 2-3 条可用于后续 JOIN/GROUP 的演示数据。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_schema_constraints.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/learning/sql/01_create_schema.sql docs/learning/sql/02_seed_demo_data.sql tests/test_schema_constraints.py
git commit -m "feat: 增加MySQL建表脚本并验证核心约束行为"
```

### Task 3: SQL 基础 CRUD 训练（先命令行）

**本任务目的：**
- 把建好的表结构转化为可操作的数据行为能力（增删改查与聚合分析）。
- 通过结果导向测试验证 SQL 不只“能执行”，而且“结果正确”。
- 形成可复用的 SQL 练习脚本与笔记，为后续 API 查询逻辑打底。

**Files:**
- Create: `docs/learning/sql/03_crud_practice.sql`
- Create: `docs/learning/sql/04_join_and_group_practice.sql`
- Create: `docs/learning/mysql-crud-notes.md`
- Create: `tests/test_sql_crud_behavior.py`

**Step 1: Write the failing test（L2：CRUD 行为）**

Create `tests/test_sql_crud_behavior.py`，至少包含：

```python
def test_insert_update_delete_flow(self):
    # INSERT 后行数+1；UPDATE 后状态变化；DELETE 后行数恢复

def test_join_group_returns_expected_aggregation(self):
    # JOIN + GROUP BY 后，每个 task 的上传文件数与预期一致
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_sql_crud_behavior.py -v`
Expected: FAIL（SQL 脚本未完成或结果不符）

**Step 3: Write minimal implementation**

- 在 `03_crud_practice.sql` 编写可重复执行的 INSERT/SELECT/UPDATE/DELETE。
- 在 `04_join_and_group_practice.sql` 编写 JOIN、GROUP BY、HAVING、ORDER BY。
- 在 `mysql-crud-notes.md` 记录每条 SQL 的输入、输出、易错点（尤其主键冲突与 WHERE 漏写）。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_sql_crud_behavior.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/learning/sql/03_crud_practice.sql docs/learning/sql/04_join_and_group_practice.sql docs/learning/mysql-crud-notes.md tests/test_sql_crud_behavior.py
git commit -m "feat: 增加SQL CRUD与JOIN聚合行为测试"
```

### Task 4: 索引与执行计划学习（EXPLAIN）

**本任务目的：**
- 建立“索引是否生效必须可证明”的性能意识，而非凭经验加索引。
- 学会通过 `EXPLAIN` 的 `type/key/rows/extra` 判断查询路径质量。
- 将索引实验结果固化为测试和笔记，形成后续排查慢 SQL 的方法论。

**Files:**
- Create: `docs/learning/sql/05_index_experiment.sql`
- Create: `docs/learning/mysql-explain-notes.md`
- Create: `tests/test_index_explain_behavior.py`

**Step 1: Write the failing test（L2：性能行为）**

Create `tests/test_index_explain_behavior.py`，至少包含：

```python
def test_explain_uses_composite_index_after_create(self):
    # 建索引前 key 为 NULL
    # 建索引后 key = idx_upload_task_file_type（或你定义的索引名）

def test_explain_rows_not_worse_after_index(self):
    # rows_after <= rows_before（在同一数据集下）
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_index_explain_behavior.py -v`
Expected: FAIL（索引未建立或查询条件不匹配索引）

**Step 3: Write minimal implementation**

- 在 `05_index_experiment.sql` 编写无索引查询、创建联合索引 `(task_id, file_type)`、再次 EXPLAIN。
- 在 `mysql-explain-notes.md` 记录 `type/key/rows/extra` 变化和“为何生效/为何不生效”。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_index_explain_behavior.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/learning/sql/05_index_experiment.sql docs/learning/mysql-explain-notes.md tests/test_index_explain_behavior.py
git commit -m "feat: 增加索引EXPLAIN行为测试与分析"
```

### Task 5: 事务与回滚实验

**本任务目的：**
- 掌握事务原子性在本项目中的实际价值：要么全部成功，要么全部回滚。
- 用可重复测试验证 `COMMIT` 与 `ROLLBACK` 的真实差异。
- 为后续多步骤写入（任务、上传、结果）提供一致性保障思维。

**Files:**
- Create: `docs/learning/sql/06_transaction_lab.sql`
- Create: `docs/learning/mysql-transaction-notes.md`
- Create: `tests/test_transaction_behavior.py`

**Step 1: Write the failing test（L2：事务原子性行为）**

Create `tests/test_transaction_behavior.py`，至少包含：

```python
def test_rollback_keeps_database_unchanged(self):
    # START TRANSACTION 后插入2张表，触发异常并 ROLLBACK
    # 断言两张表都没有新增记录

def test_commit_persists_all_changes(self):
    # START TRANSACTION 后插入2张表并 COMMIT
    # 断言两张表都可查到新增记录
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_transaction_behavior.py -v`
Expected: FAIL（事务控制语句或异常处理不正确）

**Step 3: Write minimal implementation**

- 在 `06_transaction_lab.sql` 编写 `START TRANSACTION`、`ROLLBACK`、`COMMIT` 两组对照实验。
- 在 `mysql-transaction-notes.md` 记录“原子性如何保护 task 数据一致性”。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_transaction_behavior.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add docs/learning/sql/06_transaction_lab.sql docs/learning/mysql-transaction-notes.md tests/test_transaction_behavior.py
git commit -m "feat: 增加事务回滚与提交行为测试"
```

### Task 6: 用最小 Python 脚本直连 MySQL（不走 Flask）

**本任务目的：**
- 把“纯 SQL 能力”迁移到 Python 执行层，建立程序化访问数据库能力。
- 先理解驱动连接、参数化查询、结果处理，再进入 Web 框架抽象。
- 通过脚本行为测试确保创建/查询/更新链路在代码中可复现。

**Files:**
- Create: `scripts/mysql_learning_lab.py`
- Create: `tests/test_mysql_learning_script_behavior.py`

**Step 1: Write the failing test（L2：脚本行为）**

Create `tests/test_mysql_learning_script_behavior.py`，至少包含：

```python
def test_script_creates_task_and_updates_status(self):
    # 调用脚本核心函数（例如 run_lab）
    # 断言返回 task_id 存在，且数据库中该任务状态已被更新

def test_script_returns_structured_result(self):
    # 断言返回 dict 包含 created_task_id / selected_count / updated_rows
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_mysql_learning_script_behavior.py -v`
Expected: FAIL（脚本尚未实现可测函数或返回结构）

**Step 3: Write minimal implementation**

在 `scripts/mysql_learning_lab.py` 实现：
- 读取 `DATABASE_URL`
- 执行 3 个 SQL（创建任务、查询任务、更新状态）
- 暴露可测试函数（例如 `run_lab()`）返回结构化结果

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_mysql_learning_script_behavior.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/mysql_learning_lab.py tests/test_mysql_learning_script_behavior.py
git commit -m "feat: 增加Python直连MySQL脚本行为测试"
```

### Task 7: 将学习结果映射到 Flask（先任务接口）

**本任务目的：**
- 将前面学到的结构与行为约束映射为 API 层可用能力。
- 验证接口返回与数据库状态一致，建立“接口即数据契约”意识。
- 从最小任务接口切入，降低一次性接入 ORM 的复杂度。

**Files:**
- Modify: `app.py`
- Create: `extensions.py`
- Create: `models.py`
- Create: `tests/test_task_api.py`

**Step 1: Write the failing test（L3：接口+落库行为）**

Create `tests/test_task_api.py`，至少包含：

```python
def test_create_task_returns_task_id_and_persists(self):
    # POST /api/task/create
    # 断言 200、JSON 含 task_id，且 DB 中存在该任务

def test_get_task_returns_same_task(self):
    # 先创建，再 GET /api/task/<task_id>
    # 断言返回 task_id 与状态字段一致

def test_get_task_not_found(self):
    # 不存在 task_id 返回 404
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_task_api.py -v`
Expected: FAIL（接口或持久化未实现）

**Step 3: Write minimal implementation**

- 接入 SQLAlchemy 与模型。
- 实现 `POST /api/task/create` 与 `GET /api/task/<task_id>`。
- 确保接口和数据库状态一致。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_task_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app.py extensions.py models.py tests/test_task_api.py
git commit -m "feat: 接入Flask任务接口并通过接口落库行为测试"
```

### Task 8: 完成上传/对账/导出的 task_id 数据闭环

**本任务目的：**
- 打通上传、对账、导出全链路中的 `task_id` 主线，确保数据可追踪。
- 用端到端测试约束参数校验与任务隔离，避免跨任务数据污染。
- 在不改核心算法前提下完成持久化闭环，验证系统级一致性。

**Files:**
- Modify: `app.py`
- Modify: `static/js/app.js`
- Modify: `templates/index.html`
- Test: `tests/test_upload_api_with_task.py`
- Test: `tests/test_reconcile_api_with_task.py`
- Test: `tests/test_export_api_with_task.py`

**Step 1: Write the failing test（L3：端到端业务行为）**

分别写 3 类测试，每类至少覆盖“参数校验 + 正常路径”两种：
- 上传接口：缺少 `task_id` 返回 400；带有效 `task_id` 时写入对应任务记录。
- 对账接口：缺少 `task_id` 返回 400；有效 `task_id` 时只处理该任务数据。
- 导出接口：缺少 `task_id` 返回 400；有效 `task_id` 时只导出该任务结果。

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

**本任务目的：**
- 将零散实践沉淀为结构化能力清单，确保“会做”变成“能解释、能复用”。
- 通过文档质量测试检验学习产出，而不仅是功能完成。
- 为后续从学习阶段过渡到稳定交付阶段提供可追溯证据。

**Files:**
- Create: `docs/learning/mysql-learning-retrospective.md`
- Modify: `project.md`
- Modify: `README_使用说明.txt`

**Step 1: Write the failing test/checklist（L2：学习产出可验证）**

Create `tests/test_learning_retro_quality.py`，断言复盘文档必须包含：

1. “建表与约束理解”章节。
2. “EXPLAIN 索引分析”章节。
3. “事务回滚案例”章节。
4. “至少 3 个真实踩坑与解决方案”条目。
5. “ORM vs 原生 SQL 取舍”结论。

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
