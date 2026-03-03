# GitHub 代码版本查看指南（详细版）

本文档用于查阅两件事：

1. 如何在 GitHub 上查看你每次提交后的历史版本。
2. 如何在本地查看、切换、对比旧版本代码，并安全回到最新版。

说明：文中的每条命令都给出了「命令模板」和「实际示例」。你可以直接复制示例运行。

## 0. 先确认你在项目根目录

### 0.1 打开 VS Code 内置终端

- 快捷键：`Ctrl + \``
- 菜单：Terminal -> New Terminal

### 0.2 查看当前目录

命令模板：

```powershell
pwd
```

实际示例：

```powershell
pwd
```

示例输出（你应看到类似路径）：

```text
Path
----
D:\Reconciliation
```

### 0.3 如果不在项目目录，先切换目录

命令模板：

```powershell
cd <你的项目绝对路径>
```

实际示例：

```powershell
cd D:\Reconciliation
```

再次确认目录：

```powershell
pwd
```

## 1. 在 GitHub 网页查看历史版本

1. 打开仓库主页，例如：`https://github.com/luna328/AutoReconciliation`
2. 点击上方的 **Commits**（提交记录）。
3. 点击任意一条提交记录，进入该版本详情页。

在详情页你可以看到：

- 提交说明（这次做了什么）
- 提交人和提交时间
- 改动文件列表
- 每个文件的新增/删除行（diff）

## 2. 在本地查看提交历史（最常用）

### 2.1 查看精简历史

命令模板：

```bash
git log --oneline
```

实际示例：

```bash
git log --oneline
```

示例输出：

```text
1aeb5da feat: 优化对账结果导出
97ce78a fix: 修复日期解析问题
87298e6 chore: 初始版本
```

解释：

- `1aeb5da` 是提交号（commit hash）
- 后面是提交说明
- 越靠上越新

### 2.2 查看完整历史

命令模板：

```bash
git log
```

实际示例：

```bash
git log
```

示例输出会包含作者、日期、完整提交说明。

## 3. 查看旧版本完整代码（临时切换）

适用场景：你想把整个项目切到过去某次提交，通读当时代码。

### 3.1 先找目标提交号

命令模板：

```bash
git log --oneline
```

实际示例：

```bash
git log --oneline
```

### 3.2 切到旧版本

命令模板：

```bash
git checkout <提交号>
```

实际示例：

```bash
git checkout 97ce78a
```

此时你会进入 detached HEAD 状态，这是正常的，表示你正在查看历史快照。

### 3.3 看完后切回最新主分支

命令模板：

```bash
git checkout <主分支名>
```

实际示例（main）：

```bash
git checkout main
```

实际示例（master）：

```bash
git checkout master
```

### 3.4 不确定主分支名时，先查当前分支

命令模板：

```bash
git branch --show-current
```

实际示例：

```bash
git branch --show-current
```

示例输出：

```text
main
```

## 4. 不切版本，只看旧版本中的某个文件

适用场景：你只想看某个文件在旧提交里的内容，不想切换整个项目。

### 4.1 查看文件在某次提交的内容

命令模板：

```bash
git show <提交号>:<文件路径>
```

实际示例：

```bash
git show 97ce78a:README_使用说明.txt
```

### 4.2 查看某次提交改了哪些文件

命令模板：

```bash
git show --name-only --oneline <提交号>
```

实际示例：

```bash
git show --name-only --oneline 97ce78a
```

示例输出：

```text
97ce78a fix: 修复日期解析问题
app.py
templates/index.html
```

### 4.3 查看某次提交的详细改动

命令模板：

```bash
git show <提交号>
```

实际示例：

```bash
git show 97ce78a
```

## 5. 对比两个版本差异

### 5.1 对比两个提交之间全部差异

命令模板：

```bash
git diff <旧提交号> <新提交号>
```

实际示例：

```bash
git diff 97ce78a 1aeb5da
```

### 5.2 只看哪些文件发生变化

命令模板：

```bash
git diff --name-only <旧提交号> <新提交号>
```

实际示例：

```bash
git diff --name-only 97ce78a 1aeb5da
```

示例输出：

```text
app.py
static/js/app.js
```

## 6. 用 Tag 给重要版本做永久标记（强烈推荐）

为什么要用 tag：

- 提交号不好记，tag 好记（例如 `v1.0.1`）
- 发布/回滚时更清晰
- GitHub Releases 常配合 tag 使用

### 6.1 创建标签

命令模板：

```bash
git tag -a <版本号> -m "<版本说明>"
```

实际示例：

```bash
git tag -a v1.0.1 -m "版本 v1.0.1：修复对账日期问题"
```

### 6.2 推送某一个标签到 GitHub

命令模板：

```bash
git push origin <版本号>
```

实际示例：

```bash
git push origin v1.0.1
```

### 6.3 一次性推送全部标签

命令模板：

```bash
git push origin --tags
```

实际示例：

```bash
git push origin --tags
```

### 6.4 查看全部标签

命令模板：

```bash
git tag
```

实际示例：

```bash
git tag
```

示例输出：

```text
v1.0.0
v1.0.1
```

### 6.5 切到某个标签版本

命令模板：

```bash
git checkout <版本号>
```

实际示例：

```bash
git checkout v1.0.1
```

看完后回到主分支：

```bash
git checkout main
```

## 7. 一套可直接执行的完整流程（查看旧版本并回到最新版）

按顺序执行：

```bash
pwd
git log --oneline
git checkout 97ce78a
git show --name-only --oneline 97ce78a
git checkout main
git log --oneline
```

每行示例说明：

- `pwd`：确认你在正确目录
- `git log --oneline`：找提交号
- `git checkout 97ce78a`：切到旧版本
- `git show --name-only --oneline 97ce78a`：看这次改了哪些文件
- `git checkout main`：回到最新版
- `git log --oneline`：确认当前已回到主线历史

## 8. 常见问题（FAQ）

### Q1: 每次 push 后，GitHub 会自动保存旧版本吗？

会。只要你是正常 `commit + push`，GitHub 会保留提交历史。

示例命令：

```bash
git add .
git commit -m "fix: 修复对账金额匹配"
git push origin main
```

### Q2: 哪些操作可能让旧历史看起来“消失”？

改写历史类操作，例如强推：

```bash
git push --force
```

日常不建议使用该命令。

### Q3: 我经常说“pull 到 GitHub”，对吗？

不对。术语如下：

- 上传到 GitHub：`push`
- 从 GitHub 拉到本地：`pull`

示例命令：

```bash
git push origin main
git pull origin main
```

## 9. 维护建议（长期可追溯）

1. 每次改动都做提交：

```bash
git add .
git commit -m "feat: 本次改动说明"
```

2. 每周或每次发布打 tag：

```bash
git tag -a v1.0.2 -m "版本 v1.0.2"
git push origin v1.0.2
```

3. 上传前先看状态，避免漏传：

```bash
git status
```

4. 上传后检查是否成功：

```bash
git log --oneline -n 3
```

---

如果你后续需要，我可以再补一份《只保留最常用 12 条命令的速查卡》。
