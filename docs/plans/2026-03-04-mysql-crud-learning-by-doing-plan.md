# MySQL CRUD 边做边学计划单

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在当前项目真实表结构上系统掌握 CRUD，并把 SQL 能力直接转化为可测试、可落库、可复盘的工程能力。

**Architecture:** 以“真实业务表 + 行为测试 + 文档复盘”为主线推进。每个学习单元都包含：目标 SQL、最小失败测试、最小实现、验证命令、学习笔记。先保证结果正确（L2），再补性能意识（L3）。

**Tech Stack:** MySQL 8, Python unittest, PyMySQL, mysql client

---

## 适用项目上下文

- 当前核心表：`reconcile_task`、`upload_record`、`reconcile_result`
- 当前已完成：Task 1（环境契约）、Task 2（约束行为测试）、Task 3（基础 CRUD + JOIN/GROUP 行为测试）
- 本计划重点：深化 CRUD 能力，不急着扩展新功能

---

## 学习原则（边做边学）

- 每次学习只做一个闭环：**写失败测试 -> 实现 SQL -> 运行验证 -> 记录结论**。
- 优先验证“行为正确”，避免只做“文件存在”检查。
- 所有练习都绑定项目真实表，避免脱离业务场景。
- 每完成一个单元，产出可复用脚本和笔记。

---

### Unit 1：Create 进阶（插入与幂等）

**目标：** 掌握单条插入、批量插入、避免重复插入。

**Files:**
- Create: `docs/learning/sql/07_create_advanced.sql`
- Create: `tests/test_create_behavior.py`
- Modify: `docs/learning/mysql-crud-notes.md`

**Step 1: Write the failing test**

在 `tests/test_create_behavior.py` 编写至少 2 个测试：
1. 插入后行数增加、能查到最新任务。
2. 幂等插入场景（同名任务策略）符合预期（拒绝或允许，必须明确）。

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_create_behavior.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 在 `07_create_advanced.sql` 实现：
  - 单条 `INSERT`
  - 批量 `INSERT`
  - 一种幂等策略（例如先查后插、或约束后处理）

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_create_behavior.py -v`
Expected: PASS

**Step 5: Notes + Commit**

- 在 `docs/learning/mysql-crud-notes.md` 新增“Create 进阶”小节。

---

### Unit 2：Read 进阶（过滤、排序、分页）

**目标：** 掌握可控查询，不再停留在 `SELECT *`。

**Files:**
- Create: `docs/learning/sql/08_read_advanced.sql`
- Create: `tests/test_read_behavior.py`
- Modify: `docs/learning/mysql-crud-notes.md`

**Step 1: Write the failing test**

在 `tests/test_read_behavior.py` 编写至少 3 个测试：
1. 按状态过滤返回正确集合。
2. 按 `created_at DESC` 排序正确。
3. 分页（`LIMIT/OFFSET`）返回条数与顺序正确。

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_read_behavior.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 在 `08_read_advanced.sql` 实现过滤、排序、分页 SQL。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_read_behavior.py -v`
Expected: PASS

**Step 5: Notes + Commit**

- 在笔记补充“查询正确性检查清单”（过滤、排序、分页）。

---

### Unit 3：Update 进阶（精准更新与安全更新）

**目标：** 避免误更新，掌握条件更新与幂等更新。

**Files:**
- Create: `docs/learning/sql/09_update_advanced.sql`
- Create: `tests/test_update_behavior.py`
- Modify: `docs/learning/mysql-crud-notes.md`

**Step 1: Write the failing test**

在 `tests/test_update_behavior.py` 编写至少 2 个测试：
1. 仅目标任务被更新（非目标记录不受影响）。
2. 幂等更新（已是 `done` 时再次更新不改变结果）。

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_update_behavior.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 在 `09_update_advanced.sql` 实现 `WHERE` 精准更新和幂等更新条件。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_update_behavior.py -v`
Expected: PASS

**Step 5: Notes + Commit**

- 在笔记补充“UPDATE 风险案例”（漏写 WHERE、覆盖更新）。

---

### Unit 4：Delete 进阶（安全删除与级联影响）

**目标：** 理解删除行为、级联影响和恢复难度。

**Files:**
- Create: `docs/learning/sql/10_delete_advanced.sql`
- Create: `tests/test_delete_behavior.py`
- Modify: `docs/learning/mysql-crud-notes.md`

**Step 1: Write the failing test**

在 `tests/test_delete_behavior.py` 编写至少 2 个测试：
1. 删除目标 task 后，`upload_record` 级联删除生效。
2. 非目标任务及其记录不受影响。

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_delete_behavior.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 在 `10_delete_advanced.sql` 编写删除 SQL 和删除前确认查询。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_delete_behavior.py -v`
Expected: PASS

**Step 5: Notes + Commit**

- 在笔记补充“DELETE 安全清单”（先查后删、事务保护）。

---

### Unit 5：CRUD + 事务组合演练

**目标：** 在一个业务流程中串联 C/U/D，理解原子性。

**Files:**
- Create: `docs/learning/sql/11_crud_with_transaction.sql`
- Create: `tests/test_crud_transaction_flow.py`
- Modify: `docs/learning/mysql-crud-notes.md`

**Step 1: Write the failing test**

在 `tests/test_crud_transaction_flow.py` 编写至少 2 个测试：
1. 中途异常后回滚，数据库保持原状态。
2. 全流程成功后提交，所有目标状态一致。

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_crud_transaction_flow.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 在 `11_crud_with_transaction.sql` 编写 `START TRANSACTION/COMMIT/ROLLBACK` 对照流程。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_crud_transaction_flow.py -v`
Expected: PASS

**Step 5: Notes + Commit**

- 在笔记补充“事务保护 CRUD 的案例与边界”。

---

### Unit 6：CRUD 接口映射（与 Flask 接口对齐）

**目标：** 把 SQL CRUD 能力映射到 API，验证接口与数据库一致。

**Files:**
- Modify: `tests/test_task_api.py`
- Create: `tests/test_task_crud_api_behavior.py`
- Modify: `docs/learning/mysql-crud-notes.md`

**Step 1: Write the failing test**

新增接口行为测试：
1. 创建任务后可查回。
2. 更新任务状态后 DB 状态同步。
3. 删除任务后级联结果符合预期。

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_task_crud_api_behavior.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**

- 在已有接口代码上补最小改造，使 API 行为与 SQL 规则一致。

**Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_task_crud_api_behavior.py -v`
Expected: PASS

**Step 5: Notes + Commit**

- 在笔记补充“SQL 行为与 API 行为映射关系”。

---

## 每日执行模板（建议）

- 20 分钟：写失败测试（Red）
- 30 分钟：写最小 SQL/代码实现（Green）
- 10 分钟：整理笔记与易错点
- 5 分钟：记录今日结论与明日风险

---

## 验收标准（CRUD 学习达标）

- 你能解释并演示 C/R/U/D 的正确性与风险点（不是只会写语句）。
- 你能用测试证明外键、唯一约束、级联和事务行为生效。
- 你能把 SQL 行为映射到 API 行为，并定位不一致问题。
- 你产出完整脚本、测试、笔记三件套，可复用可回归。

---

## 推荐执行顺序（结合当前进度）

1. Unit 1 -> Unit 2 -> Unit 3 -> Unit 4（先扎实 CRUD）
2. Unit 5（事务组合）
3. Unit 6（映射到 API）
