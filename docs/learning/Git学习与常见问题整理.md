# Git 学习与常见问题整理（基于本次沟通）

本文档整理了我们之前讨论过的 Git 关键知识点，重点覆盖你提过的疑问：

- 文件保存后为什么还要 commit / push
- 本地磁盘、本地 Git 仓库、GitHub 远程仓库三者关系
- `git add .` 的含义与空格问题
- 常规开发提交流程
- push 到 `main` 与 push 到分支的区别
- 为什么 push 前常要先 pull（即使文件已在本地磁盘）
- `origin` 和 `-u` 的含义
- `git pull` 冲突：为什么发生、出现什么场景、如何处理

---

## 1. 三层结构：本地磁盘 / 本地 Git 仓库 / GitHub 远程仓库

你现在的理解是正确的：这三层是独立的。

1. **本地磁盘（工作区）**
   - 你在编辑器里看到和修改的真实文件。
   - 点击保存，只是写入磁盘，不会自动进入版本历史。

2. **本地 Git 仓库（版本库）**
   - 通过 `commit` 记录版本快照。
   - 包含提交历史、作者、时间、提交说明、父子关系。

3. **GitHub 远程仓库**
   - 团队共享的远程副本。
   - 通过 `push` 接收本地已提交的 commit。

关系图：

```text
[本地磁盘工作区]
   (改代码/保存文件)
          |
          | git add + git commit
          v
[本地 Git 仓库]
   (本地版本历史)
          |
          | git push
          v
[GitHub 远程仓库]
   (团队共享)
```

反向同步：

```text
[GitHub 远程仓库]
          |
          | git pull   (或 fetch + merge/rebase)
          v
[本地 Git 仓库 + 本地磁盘]
```

---

## 2. 为什么要先 commit 再 push

### 2.1 核心原因
- `push` 传的是 **commit 记录**，不是你磁盘里的临时改动。
- 没有 commit，就没有可 push 的新版本。

### 2.2 如果不 commit 直接 push 会怎样
常见结果：

1. **远程没有任何变化**（通常显示 `Everything up-to-date`）。
2. 若本地有旧 commit，会推送旧 commit，但你最新未提交改动不会上传。
3. Git 不会把未提交改动偷偷带上去。

一句话：**GitHub 只认 commit，不认未提交改动。**

### 2.3 push 到底同步什么（你新确认的关键点）

push 同步的不是“某一个文件”或“仅上一个 commit 的内容”，而是：

- **当前本地分支上，远程分支还没有的 commit 集合**（通常是一段连续提交链）。

例如：

- 远程在 `A`
- 本地在 `C`
- 本地比远程多了 `B -> C` 两个 commit

执行一次 `git push` 后，远程会从 `A` 直接前进到 `C`，并同时包含 `B` 和 `C`。

示意：

```text
push 前：origin/main -> A，local main -> C（A-B-C）
push 后：origin/main -> C（包含 A-B-C）
```

一句话记忆：
**push 同步的是提交历史差异，不是单个文件差异。**

---

## 3. 本地 Git 仓库为什么必需

“不能直接从本地磁盘 push 到 GitHub 吗？”

不建议、也不符合 Git 设计。原因是：

1. **磁盘只存当前状态，不存版本语义**
   - 没有“这次改了什么、为什么改、和谁关联”。

2. **Git 本地仓库存的是版本数据库**
   - 支持分支、回滚、差异比较、合并、审计。

3. **支持原子提交与离线工作**
   - 你可以先本地整理成一条清晰 commit，再统一推送。

4. **协作与 Code Review 依赖 commit**
   - PR、CI、变更追踪都基于提交历史。

---

## 4. `git add .` 是什么？为什么有空格

命令：

```bash
git add .
```

含义：把当前目录（`.`）及子目录下的改动加入暂存区。

### 4.1 为什么 `add` 和 `.` 中间要有空格
- 命令行通过空格拆分参数。
- `git add .` 解析为：`git`（程序）+ `add`（子命令）+ `.`（路径参数）。
- 如果写成 `git add.`，会被当成错误的子命令或参数。

### 4.2 常见 add 对比
- `git add .`：当前目录下新增+修改（删除在部分场景不直观）。
- `git add -A`：全仓库新增/修改/删除都加入暂存区。
- `git add -u`：只处理已跟踪文件的修改和删除，不包含新文件。

---

## 5. 常规修改后提交流程（推荐）

最常用简版：

```bash
git status
git add .
git commit -m "feat: xxx"
git push origin main
```

更稳妥工程化版（推荐）：

```bash
git status
git diff
git add .
git status
git commit -m "feat: xxx（说明为什么改）"
git push origin <当前分支>
```

建议：
- commit 前看 `git status`，避免把临时文件带进去。
- push 前看当前分支：`git branch --show-current`。
- 命令要分行执行，不要连写成一行无空格字符串。

---

## 5.1 为什么 push 前常要先 pull（即使文件在本地磁盘）

这是一个非常容易混淆的点。

- **本地磁盘有文件**，只代表你有“当前文件内容”。
- **能否 push 成功**，取决于你和远程仓库的“提交历史是否可快进（fast-forward）”。

也就是说，push 看的不是“你本地有没有文件”，而是“你的提交链是否基于远程最新提交”。

典型情况：

1. 你本地改好了文件并 commit。
2. 同事这时已经向远程 `main` 推了新 commit。
3. 你直接 `git push origin main`，可能被拒绝（non-fast-forward）。

所以常规建议先：

```bash
git pull origin main
```

先把远程最新历史同步下来并合并，再 push，成功率更高，也更不容易把冲突留到最后一步。

一句话：
**pull 是同步历史，push 是上传历史；磁盘文件只是工作结果，不等于历史同步。**

---

## 5.2 你提到的命令串写法纠正

你问到这段：

```text
git checkout maingit pull origin maingit add .git commit -m "fix: xxx"git push origin main
```

应当拆成多条命令分别执行：

```bash
git checkout main
git pull origin main
git add .
git commit -m "fix: xxx"
git push origin main
```

原因：命令行用空格和换行来分隔参数与命令，连在一起会被当成非法输入。

---

## 6. push 到 main 和 push 到分支的区别

### 6.1 push 到 `main`
- 直接进入主干。
- 速度快，但风险高。
- 一旦出问题，影响全员。

### 6.2 push 到功能分支（推荐）
- 先在分支开发，再提 PR 合并到 `main`。
- 可先 review、跑 CI、再合并，风险更低。

### 6.3 命令示例

直接推主干：

```bash
git checkout main
git pull origin main
git add .
git commit -m "fix: xxx"
git push origin main
```

分支协作（推荐）：

```bash
git checkout -b feature/footer-detect
git add .
git commit -m "feat: add flexible footer detection"
git push -u origin feature/footer-detect
# 然后在 GitHub 发起 PR: feature/footer-detect -> main
```

---

## 6.1 `origin` 和 `-u` 是什么

### `origin` 是什么
- `origin` 是远程仓库的默认别名（通常指你 clone 下来的 GitHub 地址）。
- 可通过 `git remote -v` 查看实际 URL。

例如：

```bash
git push origin main
```

表示把本地 `main` 推送到名为 `origin` 的远程仓库的 `main` 分支。

### `-u` 是什么
- `-u` 等于 `--set-upstream`，用于建立“本地分支 <-> 远程分支”的跟踪关系。
- 常用于第一次推新分支。

例如：

```bash
git push -u origin feature/footer-detect
```

执行后该本地分支会记住上游分支，后续你在这个分支通常可直接：

```bash
git push
git pull
```

无需每次都写完整的 `origin feature/footer-detect`。

一句话记忆：
- `origin` = 推到哪里
- `-u` = 记住这条路

---

## 7. `git pull` 冲突详解

这是你重点问到的内容，下面详细展开。

### 7.1 `git pull` 做了什么
`git pull` 本质上是：

1. `git fetch`：拉取远程最新提交到本地引用。
2. `git merge`（或 rebase）：把远程改动合并到当前分支。

### 7.2 为什么会冲突
冲突通常发生在：

- 同一个文件；
- 同一段或相邻代码；
- 本地和远程都改了，且改法不兼容。

Git 无法判断“该保留哪边”时，就会停下来让你手工决定。

### 7.3 冲突时会看到什么
终端常见提示：

- `CONFLICT (content): Merge conflict in xxx`
- `Automatic merge failed; fix conflicts and then commit the result.`

`git status` 会显示 `both modified` 或 `unmerged paths`。

文件里会出现标记：

```text
<<<<<<< HEAD
本地内容
=======
远程内容
>>>>>>> origin/main
```

### 7.4 常见冲突场景
1. 你和同事同时改了同一函数同一段。
2. 双方都改了 import 区域或配置文件同一字段。
3. 你删除一段代码，同事在远程修改了这段代码。
4. 你重命名文件，同事改了旧文件内容。

### 7.5 冲突怎么解决（标准步骤）
1. 运行 `git status` 找到冲突文件。
2. 打开冲突文件，人工选择：保留本地、保留远程、或手工融合。
3. 删除冲突标记（`<<<<<<<`、`=======`、`>>>>>>>`）。
4. 保存后执行 `git add <冲突文件>`。
5. 再 `git status` 确认没有 unmerged。
6. 完成合并：
   - merge 流程：`git commit`
   - rebase 流程：`git rebase --continue`
7. 最后 `git push`。

### 7.6 如何减少冲突
- 开工前先 `git pull`。
- 小步提交、尽快推送分支。
- 大改动前先和同事约定文件边界。
- 对高频冲突文件（配置、路由）提前沟通。

---

## 8. 建议掌握的常用命令（入门必备）

- `git status`：看当前状态
- `git diff`：看未暂存改动
- `git diff --staged`：看已暂存改动
- `git add <file>` / `git add .`：加入暂存区
- `git commit -m "..."`：提交
- `git pull`：拉取远程
- `git push`：推送远程
- `git log --oneline --graph --decorate -20`：看简洁历史图

常见“撤销”命令：

- `git restore <file>`：撤销工作区改动
- `git restore --staged <file>`：从暂存区撤回
- `git revert <commit>`：安全反向提交（适合已推送历史）

---

## 8.1 Git、Git Bash、GitHub 三者关系

这三个名字容易混淆，可以这样记：

- **Git**：版本控制工具本体（`add/commit/push` 都是它的命令）。
- **GitHub**：托管 Git 仓库的远程平台（代码托管、PR、Issue、协作）。
- **Git Bash**：Windows 上常用的命令行环境，方便执行 Git 和 Bash 命令。

关系图：

```text
你（在终端输入命令）
        |
        v
      Git（本地版本管理）
        |
        v
   GitHub（远程协作平台）
```

说明：
- 你不一定必须用 Git Bash，也可用 PowerShell/CMD；
- 关键是系统里要安装 Git，终端只是执行入口。

---

## 8.2 使用 Git 命令行的前提条件

使用 Git 命令前，最小前提有 3 个：

1. 电脑已安装 Git（Windows 常装 Git for Windows）。
2. 打开终端（Git Bash / PowerShell / CMD 均可）。
3. 当前目录是 Git 仓库，或先初始化/克隆仓库。

### 快速检查步骤

1) 验证 Git 是否安装

```bash
git --version
```

2) 首次配置身份（只需一次）

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

3) 准备仓库

- 新建仓库：

```bash
git init
```

- 克隆远程仓库：

```bash
git clone <仓库地址>
```

4) 日常最小流程

```bash
git status
git add .
git commit -m "feat: xxx"
git push
```

一句话：
**先安装 Git，再进入仓库目录，就能在终端使用 Git 命令。**

---

## 8.3 `feat`、`fix` 等提交前缀是什么

你问到的 `feat`、`fix` 是 commit message 的“类型前缀”，常见于 **Conventional Commits** 规范。

作用：
- 让团队快速看懂这次提交属于什么变更类型；
- 便于自动生成变更日志（changelog）；
- 便于版本发布工具做自动化判断。

常见前缀：

- `feat`：新功能
- `fix`：修复缺陷
- `docs`：文档更新
- `style`：代码格式/样式调整（不改逻辑）
- `refactor`：重构（不新增功能、不修 bug）
- `test`：测试相关
- `chore`：杂项维护（依赖、脚本、配置）
- `perf`：性能优化
- `ci`：CI/CD 配置变更
- `build`：构建系统/打包相关变更
- `revert`：回滚某次提交

常见格式：

```text
<type>: <简短说明>
```

例如：

```text
feat: 支持入库单表尾多规则识别
fix: 修复金额差异误分类
docs: 更新Git学习文档
refactor: 抽取表尾识别公共函数
```

关于 `feat/fix` 这种写法：
- 能表达“同时有功能和修复”；
- 但更推荐按主要变更类型写一条，或拆成两条 commit，便于历史清晰和统计。

---

## 9. 一句话总复盘

你当前最关键认知已经建立：

- **save 是保存文件**
- **commit 是保存版本**
- **push 是上传版本到远程**

而冲突处理的核心就是：

- Git 负责发现冲突
- 你负责按业务语义裁决冲突
- 裁决后再 add/commit/push 完成闭环
