-- 1) 创建一个用于 JOIN/GROUP 的任务
INSERT INTO reconcile_task (task_name, status)
VALUES ('tdd-join-task', 'created');
-- 2) 取刚插入任务 ID（用用户变量承接）
SET @task_id = LAST_INSERT_ID();
-- 3) 插入两条上传记录
INSERT INTO upload_record (task_id, file_type, file_name)
VALUES
(@task_id, 'left', 'join_left.csv'),
(@task_id, 'right', 'join_right.csv');
-- 4) JOIN + GROUP BY: 每个任务对应上传记录数量
SELECT
    t.id,
    t.task_name,
    COUNT(u.id) AS upload_count
FROM reconcile_task t
LEFT JOIN upload_record u ON u.task_id = t.id
WHERE t.task_name = 'tdd-join-task'
GROUP BY t.id, t.task_name
HAVING COUNT(u.id) >= 2
ORDER BY t.id DESC;