# Task 1 实施记录（开发驱动学习）

## 1. 任务目标
Task 1 的初始目标是：
- 建立一个最小的学习资产（`mysql-learning-checklist.md`）。
- 通过 TDD 的 RED -> GREEN 节奏，先练习“测试驱动”的基本动作。

说明：本任务更偏“流程训练”，不是最终业务功能实现。

---

## 2. 本次实际执行步骤

### 步骤 A：创建测试文件（RED）
- 创建文件：`tests/test_mysql_learning_assets.py`
- 初始测试逻辑：检查 `docs/learning/mysql-learning-checklist.md` 是否存在。

测试代码核心断言：

```python
self.assertTrue(os.path.exists("docs/learning/mysql-learning-checklist.md"))
```

### 步骤 B：运行测试并观察失败
执行命令（最终正确方式）：

```bat
python -m unittest -v tests.test_mysql_learning_assets
```

首次得到 `FAIL`，原因：目标 markdown 文件尚未创建。

### 步骤 C：最小实现（GREEN）
- 创建文件：`docs/learning/mysql-learning-checklist.md`
- 写入最小内容（安装、建库、授权、连通性检查项）

### 步骤 D：再次运行测试
执行命令：

```bat
python -m unittest -v tests.test_mysql_learning_assets
```

测试通过（`OK`）。

---

## 3. 过程中使用的关键命令与含义

### 3.1 测试执行命令

```bat
python -m unittest -v tests.test_mysql_learning_assets
```

含义：
- `python -m unittest`：通过 Python 内置单元测试框架运行测试。
- `-v`：详细输出（看到测试函数名和结果）。
- `tests.test_mysql_learning_assets`：指定测试模块路径（包.模块）。

为什么这样写：
- 避免路径写法导致导入错误。
- 比直接传 `tests/xxx.py` 在当前项目结构下更稳定。

### 3.2 目录检查命令

```bat
dir
dir tests
```

含义：
- 查看当前目录内容，核对文件和目录是否存在。

用途：
- 排查“文件明明创建了但测试找不到”的问题。

### 3.3 目录重命名命令（排错）

```bat
ren tsets tests
```

含义：
- 将误拼写目录 `tsets` 重命名为 `tests`。

用途：
- 修复 `ModuleNotFoundError: No module named 'tests'`。

---

## 4. 本任务实现了什么功能

已实现：
- 测试框架可运行（能够定位指定测试模块）。
- 已建立一个 MySQL 学习清单文档。
- 已完成一次完整 TDD 最小循环（RED -> GREEN）。

未实现：
- 真实数据库行为验证（如连接 MySQL、执行 SQL、校验权限）。
- 业务 API 或持久化逻辑改造。

---

## 5. 本任务的意义与边界

### 5.1 意义
- 帮助建立 TDD 操作习惯：先失败、再最小实现、再通过。
- 暴露并解决测试运行基础问题（模块导入、目录命名、命令格式）。
- 形成学习资产文档，便于后续复盘。

### 5.2 边界（重要）
- 当前这个测试价值偏“流程验证”，对业务驱动较弱。
- 仅检查文件存在，不能证明数据库能力已打通。

因此后续 Task 2+ 应升级为“真实价值测试”，例如：
- 测试 `DATABASE_URL` 可读取。
- 测试 `recon_user` 可连库并 `SELECT 1`。
- 测试创建任务后数据库确实新增记录。

---

## 6. 本次踩坑与结论

- 坑 1：把终端命令当成 SQL 在 `mysql>` 里执行。
  - 结论：`mysql -u ...` 是系统终端命令，不是 SQL。

- 坑 2：测试目录误拼写为 `tsets`。
  - 结论：导入错误先查目录与模块名是否一致。

- 坑 3：测试命令参数写法不当导致模块导入失败。
  - 结论：优先使用模块路径方式运行 unittest。

---

## 7. 下一步建议

下一步不再停留在“文件存在”测试，改为真实数据库驱动测试：
1. 写失败测试：读取 `DATABASE_URL` 并尝试 MySQL 连接。
2. 写最小实现：新增 Python 连接辅助代码（或最小脚本）。
3. 测试通过后再进入 API 层改造。
