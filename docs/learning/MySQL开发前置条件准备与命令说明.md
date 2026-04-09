# MySQL开发前置条件准备与命令说明

## 1. 文档目的
本文件用于回顾我们在“本地 MySQL + 项目接库”前做过的准备工作，说明每一步为什么需要、用了哪些命令、命令分别代表什么。

---

## 2. 为什么要做前置条件准备

在接数据库前，先做环境准备可以避免三类常见问题：

- 代码还没写就连不上库（端口、账号、权限、服务未启动）。
- 代码写好了但行为不可复现（环境变量缺失、连接串不统一）。
- 学到了框架用法但没学到数据库本质（不会用 SQL 验证问题）。

这也是“开发驱动学习”的核心：先保证基础设施可用，再通过小步开发验证知识点。

---

## 3. 已完成的前置条件与命令回顾

### 3.1 确认 MySQL 客户端可用

在 Windows 终端（CMD/PowerShell）执行：

```bat
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" --version
```

含义：
- 检查 `mysql` 客户端是否安装成功。
- 同时确认版本（如 `8.0.45`）。

为什么要做：
- 这是最基础的“工具可用性”检查。
- 如果这一步失败，后续所有 SQL 命令都无法执行。

---

### 3.2 以 root 登录 MySQL

```bat
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

含义：
- `-u root` 指定数据库用户。
- `-p` 表示输入该用户密码。

为什么要做：
- root 账号通常有创建库、建用户、授权等管理能力。
- 第一次初始化数据库时需要管理员权限。

---

### 3.3 创建学习用数据库

在 `mysql>` 交互界面执行：

```sql
CREATE DATABASE IF NOT EXISTS reconciliation_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

含义：
- 创建名为 `reconciliation_dev` 的数据库。
- 使用 `utf8mb4` 保证中文和特殊字符兼容。

为什么要做：
- 让开发和学习有独立数据库，避免污染系统库。
- 统一字符集，减少后续中文字段乱码风险。

---

### 3.4 创建并授权业务账号（最小隔离）

```sql
CREATE USER IF NOT EXISTS 'recon_user'@'localhost' IDENTIFIED BY '你的密码';
CREATE USER IF NOT EXISTS 'recon_user'@'127.0.0.1' IDENTIFIED BY '你的密码';

ALTER USER 'recon_user'@'localhost' IDENTIFIED BY '你的密码';
ALTER USER 'recon_user'@'127.0.0.1' IDENTIFIED BY '你的密码';

GRANT ALL PRIVILEGES ON reconciliation_dev.* TO 'recon_user'@'localhost';
GRANT ALL PRIVILEGES ON reconciliation_dev.* TO 'recon_user'@'127.0.0.1';
FLUSH PRIVILEGES;
```

含义：
- 创建/重置本地学习账号。
- 对指定数据库授予权限。
- `FLUSH PRIVILEGES` 让权限变更立即生效。

为什么要做：
- 开发不建议长期使用 root。
- `localhost` 与 `127.0.0.1` 在 MySQL 授权中是不同 host 维度，双配置可减少登录歧义。

---

### 3.5 验证数据库与权限

```sql
SHOW DATABASES;
USE reconciliation_dev;
SELECT 1;
```

含义：
- `SHOW DATABASES`：确认数据库是否存在。
- `USE reconciliation_dev`：切换到目标库。
- `SELECT 1`：最小连通性测试。

为什么要做：
- 证明“数据库存在 + 权限可用 + 基本 SQL 可执行”。

---

### 3.6 使用业务账号验证登录

在 Windows 终端执行：

```bat
"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u recon_user -p -h 127.0.0.1 -P 3306
```

登录后执行：

```sql
USE reconciliation_dev;
SELECT 1;
```

含义：
- 用非 root 账号验证真实开发连接路径。

为什么要做：
- 后续应用会用该账号连接数据库，这一步是“应用前置验证”。

---

### 3.7 验证 Python 运行环境

在项目根目录执行：

```bat
cd /d D:\Reconciliation
python --version
```

含义：
- 确认 Python 可执行，版本满足项目依赖要求（本次为 3.12.x）。

为什么要做：
- 后续会运行 Flask、测试、迁移命令，Python 不正常会直接阻断流程。

---

### 3.8 配置项目连接串（.env）

文件：`D:\Reconciliation\.env`

示例：

```env
DATABASE_URL=mysql+pymysql://recon_user:你的密码@127.0.0.1:3306/reconciliation_dev
FLASK_APP=app.py
```

含义：
- `DATABASE_URL`：应用连接数据库的统一入口。
- `FLASK_APP`：Flask 命令默认入口文件。

为什么要做：
- 连接信息配置化，避免写死在代码。
- 可在不同机器/环境复用同一份代码。

---

### 3.9 防止敏感信息误提交

文件：`D:\Reconciliation\.gitignore`

应包含：

```gitignore
.env
```

含义：
- Git 忽略 `.env`，避免数据库账号密码被提交到仓库。

为什么要做：
- 基础安全要求，尤其是后续推送到远程仓库时。

---

## 4. 本次踩坑复盘（关键学习点）

- `mysql -u ...` 是系统终端命令，不是 `mysql>` 内的 SQL。
- 当 `mysql>` 变成 `->` 时，表示 SQL 语句未结束（通常少了 `;`）。
- `localhost` 与 `127.0.0.1` 对应的账号权限可能不同，授权要看 host。

---

## 5. 当前状态结论

前置条件已具备，达到“可以开始学习导向开发任务”的标准：

- MySQL 可用，数据库已创建。
- 业务账号可登录并可访问目标库。
- Python 环境正常。
- 项目连接配置已准备。
- 基础安全（`.env` 忽略）已考虑。

下一步可进入学习计划 Task 1：先写失败测试并建立 MySQL 学习清单文档。

---

## 6. PATH 路径配置 vs 环境变量配置（重点区分）

### 6.1 两者不是一回事

- PATH 路径配置：告诉操作系统“去哪里找可执行程序（如 `mysql.exe`）”。
- 项目环境变量配置（如 `.env`）：告诉应用“连接什么数据库、用什么参数”。

一句话区分：
- PATH 解决“命令能不能被找到”。
- `.env` 解决“命令找到后要连哪里、怎么连”。

### 6.2 为什么不用全路径会报错

当你在终端输入：

```bat
mysql -u root -p
```

系统会按 PATH 中登记的目录顺序查找 `mysql.exe`。如果 PATH 没包含：

`C:\Program Files\MySQL\MySQL Server 8.0\bin`

就会报类似错误：
- `'mysql' 不是内部或外部命令`
- `'mysql' is not recognized as an internal or external command`

你之前用全路径可以成功，是因为绕过了 PATH 搜索，直接告诉系统可执行文件的绝对位置。

### 6.3 如何设置 PATH（Windows 图形界面方式）

1. 打开“开始菜单” -> 搜索“环境变量”。
2. 进入“编辑系统环境变量” -> “环境变量”。
3. 在“用户变量”中找到 `Path`，点击“编辑”。
4. 点击“新建”，添加：

`C:\Program Files\MySQL\MySQL Server 8.0\bin`

5. 确认保存后，关闭并重新打开终端。
6. 验证：

```bat
mysql --version
where mysql
```

若成功显示版本和路径，说明 PATH 生效。

### 6.4 如何设置 PATH（命令行方式，可选）

在 CMD（当前用户）执行：

```bat
setx PATH "%PATH%;C:\Program Files\MySQL\MySQL Server 8.0\bin"
```

说明：
- `setx` 是永久写入，需重开终端生效。
- 如果你不熟悉命令行改 PATH，优先用图形界面更稳。

### 6.5 PATH 与 .env 的典型协作关系

- PATH 正确后，你可以直接在任意终端执行 `mysql`。
- `.env` 正确后，Flask/脚本可以通过 `DATABASE_URL` 正确连接数据库。
- 两者缺一不可：
  - 只有 PATH：你能手动连库，但应用未必能连。
  - 只有 `.env`：应用参数对了，但你在终端直接跑 `mysql` 可能仍报找不到命令。

### 6.6 通用 PATH 配置方式与作用（跨工具通用）

#### 6.6.1 PATH 的通用作用

PATH 本质是一个“可执行程序搜索目录列表”。

常见作用：
- 让你在任意目录直接运行命令（如 `python`、`node`、`git`、`mysql`）。
- 避免每次都写绝对路径（减少输入和出错概率）。
- 统一团队命令使用方式（文档里写 `mysql` 即可，不用写机器相关路径）。

#### 6.6.2 常见配置方式

1) 图形界面配置（最适合初学者）
- Windows：系统设置 -> 环境变量 -> Path -> 新增目录。
- macOS/Linux：通常通过 shell 配置文件（如 `~/.zshrc`、`~/.bashrc`）写入。

2) 命令行临时配置（仅当前终端会话）
- Windows CMD：

```bat
set PATH=%PATH%;C:\your\tool\bin
```

- PowerShell：

```powershell
$env:Path += ";C:\your\tool\bin"
```

- Linux/macOS Bash：

```bash
export PATH="$PATH:/your/tool/bin"
```

用途：临时验证某工具能否运行，不改系统永久配置。

3) 命令行永久配置（当前用户）
- Windows CMD：

```bat
setx PATH "%PATH%;C:\your\tool\bin"
```

- Linux/macOS：把 `export PATH=...` 写入 `~/.bashrc` 或 `~/.zshrc`，再执行 `source` 生效。

用途：长期使用某工具，终端重启后仍可直接调用。

#### 6.6.3 验证 PATH 是否生效（通用检查）

- 看版本：

```bat
mysql --version
python --version
```

- 看命令被解析到哪里：
- Windows：

```bat
where mysql
where python
```

- Linux/macOS：

```bash
which mysql
which python
```

#### 6.6.4 PATH 排障思路（通用）

当出现“命令找不到”时，按顺序检查：

1. 工具是否真的安装了。
2. 可执行文件目录是否加入 PATH。
3. 是否重开了终端（很多改动需要新开窗口生效）。
4. PATH 中是否有多个同名程序导致优先级冲突（`where/which` 可定位）。
5. 路径是否包含空格且写法不规范（Windows 下建议加引号进行测试）。

#### 6.6.5 安全与规范建议

- 只把“工具的 bin 目录”加入 PATH，不要把过多业务目录加入。
- 不要把敏感信息放入 PATH（如密码、Token）。
- 团队项目建议在 README 统一记录“需要加入 PATH 的工具清单”。
- 如果使用虚拟环境（如 Python `.venv`），优先激活虚拟环境而不是全局乱改 PATH。

---

## 7. 学习问答补充（PATH 常见理解）

### 7.1 为什么很多软件都要配置 PATH（比如 Python）？

简化答案：
- PATH 可以理解为系统的“程序位置通讯录”。
- 你输入 `python`、`mysql`、`git` 时，系统会按 PATH 里登记的目录去找对应可执行文件。

如果不配置 PATH：
- 会出现“不是内部或外部命令 / not recognized as an internal or external command”。
- 你只能每次写完整路径，例如：

```bat
C:\Program Files\Python312\python.exe --version
```

所以配置 PATH 的作用就是：
- 在任意目录都能直接用命令名运行工具。
- 提升开发效率，减少重复输入和路径错误。

### 7.2 PATH 可以理解为“快捷方式的文字版”吗？

可以这样理解，但要更准确一点：

- 这个比喻方向是对的（大约 80%）。
- 更准确说法：PATH 不是单个快捷方式，而是“命令查找目录清单”。

区别：
- 快捷方式（`.lnk`）是一个文件指向一个程序。
- PATH 是多个目录列表；系统会按顺序在这些目录中查找同名可执行文件，找到第一个就执行。

例如输入 `python` 时，系统会按顺序搜索：
1. 当前目录
2. PATH 中配置的各目录

因此 PATH 更像“电话簿/索引表”，而不是“某一个快捷方式”。
