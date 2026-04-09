-- 1) INSERT: 新建一个任务
INSERT INTO reconcile_task (task_name, status)
VALUES ('tdd-crud-task', 'created');
-- 2) SELECT: 查询刚插入任务（用于手工观察）
SELECT id, task_name, status
FROM reconcile_task
WHERE task_name = 'tdd-crud-task'
ORDER BY id DESC
LIMIT 1;
-- 3) UPDATE: 把状态改为 done（测试会验证这一步）
UPDATE reconcile_task
SET status = 'done'
WHERE task_name = 'tdd-crud-task'
ORDER BY id DESC
LIMIT 1;
-- 4) SELECT: 再查一次确认状态已更新（用于手工观察）
SELECT id, task_name, status
FROM reconcile_task
WHERE task_name = 'tdd-crud-task'
ORDER BY id DESC
LIMIT 1;