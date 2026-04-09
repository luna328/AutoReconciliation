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