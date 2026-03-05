# MySQL 学习计划执行记录（Task 1）

## 来源
- 计划文件：`docs/plans/2026-03-04-mysql-learning-first-plan.md`
- 对应任务：Task 1（搭建本地 MySQL 学习实验环境）

## 本任务要解决什么问题
- 先建立数据库学习的最小前置条件，避免后续练习因为环境不统一而卡住。
- 用测试把“环境准备完成”变成可验证结果，而不是口头说明。
- 明确配置分工：仓库提供 `.env.example` 模板，本机使用 `.env` 或系统环境变量。

## 本次完成内容
- 新增配置模板：`.env.example`
- 完善学习清单：`docs/learning/mysql-learning-checklist.md`
- 更新 Task 1 测试：`tests/test_mysql_env.py`

## 实操步骤
1. 编写 Task 1 的测试文件，并按学习目标调整断言逻辑。
2. 创建 `.env.example`，补充 `DATABASE_URL` 和 MySQL 相关配置项。
3. 完善 `docs/learning/mysql-learning-checklist.md`，记录安装、建库授权、连接验证和配置步骤。
4. 执行单元测试，确认 Task 1 验收通过。

## 作用与意义
- `.env.example` 的作用：提供统一、可复制的配置模板，降低团队协作成本。
- `test_env_example_exists` 的作用：保证模板文件真实存在且被项目纳入管理。
- `test_database_url_key_documented` 的作用：保证关键配置入口 `DATABASE_URL` 被明确约定。
- 学习清单文档的作用：把 MySQL 前置准备转成可打勾、可复用的学习路径。

## 关键实现代码

### `tests/test_mysql_env.py`
```python
import os
import unittest


class TestMySqlEnv(unittest.TestCase):
    def test_env_example_exists(self):
        self.assertTrue(os.path.exists(".env.example"))

    def test_database_url_key_documented(self):
        with open(".env.example", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("DATABASE_URL=", content)
```

### `.env.example`
```env
DATABASE_URL=mysql+pymysql://recon_user:recon_pass@127.0.0.1:3306/reconciliation?charset=utf8mb4
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=recon_user
MYSQL_PASSWORD=recon_pass
MYSQL_DATABASE=reconciliation
```

## 命令与验证输出

### 执行命令
```bat
python -m unittest tests/test_mysql_env.py -v
```

### 实际输出
```text
test_database_url_key_documented (tests.test_mysql_env.TestMySqlEnv.test_database_url_key_documented) ... ok
test_env_example_exists (tests.test_mysql_env.TestMySqlEnv.test_env_example_exists) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.001s
```

## 结论
- Task 1 已通过测试验收，可进入 Task 2（手写建表 SQL）。

---

# MySQL 学习计划执行记录（Task 2）

## 来源
- 计划文件：`docs/plans/2026-03-04-mysql-learning-first-plan.md`
- 对应任务：Task 2（先用纯 SQL 建表，不借助 ORM）

## 本任务要解决什么问题
- 先训练“数据库第一性原理”：表结构、主外键、约束、默认值由你亲手定义。
- 在进入 Flask/ORM 之前，确保你已经能独立完成建模和落库。
- 用 SQL 脚本和测试文件把数据结构固定下来，便于后续复用和回归。

## 本次完成内容
- 新增测试文件：`tests/test_schema_sql_files.py`
- 新增建表脚本：`docs/learning/sql/01_create_schema.sql`
- 新增种子数据脚本：`docs/learning/sql/02_seed_demo_data.sql`

## 实操步骤
1. 先写失败测试，检查两个 SQL 文件是否存在。
2. 编写 `01_create_schema.sql`，创建 3 张核心表：`reconcile_task`、`upload_record`、`reconcile_result`。
3. 编写 `02_seed_demo_data.sql`，插入演示任务、上传记录、对账结果。
4. 运行单测确认文件资产就绪。
5. 使用 MySQL 命令行执行 SQL 脚本并查询结果，确认真实落库成功。

## 作用与意义
- `01_create_schema.sql`：把业务核心实体和约束关系显式化，便于理解数据一致性。
- `02_seed_demo_data.sql`：提供可重复的演示数据，方便练习 CRUD、JOIN 和调试。
- `test_schema_sql_files.py`：确保学习脚本不会被误删，保证后续任务有稳定输入。
- 命令行执行 SQL：验证你不依赖 ORM 也能直接控制数据库。

## 关键实现代码

### `tests/test_schema_sql_files.py`
```python
import os
import unittest


class TestSchemaSqlFiles(unittest.TestCase):
    def test_sql_files_exist(self):
        self.assertTrue(os.path.exists("docs/learning/sql/01_create_schema.sql"))
        self.assertTrue(os.path.exists("docs/learning/sql/02_seed_demo_data.sql"))
```

### `docs/learning/sql/01_create_schema.sql`
```sql
CREATE TABLE IF NOT EXISTS reconcile_task (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'created',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS upload_record (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_upload_task
        FOREIGN KEY (task_id) REFERENCES reconcile_task(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reconcile_result (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    result_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    diff_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_result_task UNIQUE (task_id),
    CONSTRAINT fk_result_task
        FOREIGN KEY (task_id) REFERENCES reconcile_task(id)
        ON DELETE CASCADE
);
```

### `docs/learning/sql/02_seed_demo_data.sql`
```sql
INSERT INTO reconcile_task (task_name, status)
VALUES
('demo-task-001', 'created'),
('demo-task-002', 'created');

INSERT INTO upload_record (task_id, file_type, file_name)
VALUES
(1, 'left', 'left_001.csv'),
(1, 'right', 'right_001.csv'),
(2, 'left', 'left_002.csv');

INSERT INTO reconcile_result (task_id, result_status, diff_count)
VALUES
(1, 'done', 3),
(2, 'pending', 0);
```

## 命令与验证输出

### 单元测试命令
```bat
python -m unittest tests/test_schema_sql_files.py -v
```

### 单元测试输出
```text
test_sql_files_exist (tests.test_schema_sql_files.TestSchemaSqlFiles.test_sql_files_exist) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
```

### MySQL 执行命令
```bat
mysql -u recon_user -p reconciliation < docs/learning/sql/01_create_schema.sql
mysql -u recon_user -p reconciliation < docs/learning/sql/02_seed_demo_data.sql
```

### MySQL 查询验证（关键信息）
- `SHOW TABLES;` 显示包含 `upload_record` 等目标表，说明建表成功。
- `SELECT * FROM reconcile_task;` 返回 2 行（`demo-task-001`、`demo-task-002`）。
- `SELECT * FROM upload_record;` 返回 3 行（left/right 上传记录）。
- `SELECT * FROM reconcile_result;` 返回 2 行（`done/pending` 结果）。

## 结论
- Task 2 已完成：SQL 文件创建通过测试，且脚本已在 MySQL 实际执行并验证数据落库。

---

# MySQL 学习计划执行记录（Task 2 重启版：高价值 TDD）

## 重启原因
- 原 Task 2 仅验证“文件存在”，属于 L0，无法证明数据库设计是否正确。
- 按新目标从 Task 2 开始升级为 L2 行为测试：直接验证约束和数据一致性。

## 本次测试目标（行为而非文件）
- 外键约束生效：`upload_record.task_id` 不能引用不存在任务。
- 唯一约束生效：同一 `task_id` 不能插入两条 `reconcile_result`。
- 级联删除生效：删除任务后关联 `upload_record` 自动删除。
- 结构存在：三张核心表已创建。

## 实操步骤（RED -> GREEN）
1. 先清空学习表，制造 RED 场景。
2. 编写 `tests/test_schema_constraints.py`（4 个高价值测试）。
3. 运行测试，处理中间阻塞（安装 `pymysql`、`cryptography`，修复账号认证）。
4. 用 `01_create_schema.sql` 重建表结构。
5. 重新运行测试，全部通过（GREEN）。

## 关键问题与解决
- `ModuleNotFoundError: pymysql`：安装 `pymysql`。
- `cryptography package is required`：安装 `cryptography`。
- `Access denied recon_user@localhost`：统一使用 `-h 127.0.0.1`，与测试连接主机一致。

## 命令与结果

### 关键执行命令
```bat
mysql -u recon_user -p reconciliation -e "DROP TABLE IF EXISTS reconcile_result; DROP TABLE IF EXISTS upload_record; DROP TABLE IF EXISTS reconcile_task;"
mysql -h 127.0.0.1 -u recon_user -precon_pass reconciliation < docs/learning/sql/01_create_schema.sql
python -m unittest tests/test_schema_constraints.py -v
```

### 最终测试输出
```text
test_delete_task_cascades_upload_record ... ok
test_reconcile_result_task_id_is_unique ... ok
test_tables_exist ... ok
test_upload_record_requires_existing_task ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.013s

OK
```

## 结论
- Task 2 已按高价值 TDD 通过：当前不仅“有文件”，而且关键约束行为真实可用。

## Task 2 问答补充（功能与测试作用）

### 1）两个 SQL 文件分别是什么作用
- `docs/learning/sql/01_create_schema.sql`：负责定义数据库结构（Schema），创建 `reconcile_task`、`upload_record`、`reconcile_result` 三张核心表，并声明主键、外键、唯一约束与级联删除等规则。
- `docs/learning/sql/02_seed_demo_data.sql`：负责填充演示数据（Seed Data），用于后续 CRUD/JOIN/事务练习；它不定义表结构，只插入样例记录。

### 2）`tests/test_schema_constraints.py` 在判断什么
- 判断三张核心表是否存在（结构层面）。
- 判断 `upload_record.task_id` 外键是否生效：不存在的任务 ID 不可写入上传记录。
- 判断 `reconcile_result.task_id` 唯一约束是否生效：同一任务不可重复写结果。
- 判断级联删除是否生效：删除任务后，关联上传记录会自动删除。

### 3）这些测试对表设计起什么作用
- 把“表设计意图”固化为可执行、可回归的验证规则，避免后续改动把约束悄悄破坏。
- 防止“只有表存在但行为错误”的假通过情况（例如无外键、无唯一约束）。
- 为后续 API 开发提供稳定数据契约，降低接口层出现脏数据与一致性问题的概率。

---

# MySQL 学习计划执行记录（Task 3：CRUD 与 JOIN/GROUP 行为验证）

## 来源
- 计划文件：`docs/plans/2026-03-04-mysql-learning-first-plan.md`
- 对应任务：Task 3（SQL 基础 CRUD 训练，先命令行）

## 本任务目的
- 把已建好的表结构转化为可操作的数据行为能力（CRUD + 聚合统计）。
- 用行为测试验证 SQL 脚本输出是否正确，而不是只验证文件存在。
- 沉淀可复用 SQL 练习脚本与笔记，支撑后续 API 层开发。

## 本次完成内容
- 新增行为测试：`tests/test_sql_crud_behavior.py`
- 新增 CRUD 练习脚本：`docs/learning/sql/03_crud_practice.sql`
- 新增 JOIN/GROUP 脚本：`docs/learning/sql/04_join_and_group_practice.sql`
- 新增学习笔记：`docs/learning/mysql-crud-notes.md`

## 实操步骤（RED -> GREEN）
1. 先写测试并运行，确认因 SQL 文件不存在而失败（RED）。
2. 实现 `03_crud_practice.sql`：插入任务、查询、更新状态、再次查询。
3. 实现 `04_join_and_group_practice.sql`：创建任务、插入两条上传记录、JOIN+GROUP 聚合。
4. 重新运行测试，验证两类行为都通过（GREEN）。
5. 补充 `mysql-crud-notes.md`，记录目标、结果和易错点。

## 关键测试判断点
- `test_crud_script_results`：执行 CRUD 脚本后，`tdd-crud-task` 的最终状态必须为 `done`。
- `test_join_group_script_results`：执行 JOIN/GROUP 脚本后，`tdd-join-task` 的上传记录聚合数必须为 `2`。
- 两个测试都包含清理逻辑，避免测试数据污染后续任务。

## 命令与验证输出

### 执行命令
```bat
python -m unittest tests/test_sql_crud_behavior.py -v
```

### 实际输出
```text
test_crud_script_results (tests.test_sql_crud_behavior.TestSqlCrudBehavior.test_crud_script_results) ... ok
test_join_group_script_results (tests.test_sql_crud_behavior.TestSqlCrudBehavior.test_join_group_script_results) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.015s

OK
```

## 结论
- Task 3 已完成：CRUD 与 JOIN/GROUP 练习已通过行为测试，学习产物具备可回归验证价值。
