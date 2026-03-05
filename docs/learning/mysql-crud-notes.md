# MySQL CRUD 与聚合练习笔记（Task 3）
## 1. CRUD 脚本目标与结果
- 脚本：`docs/learning/sql/03_crud_practice.sql`
- 目标：完成 INSERT -> SELECT -> UPDATE -> SELECT 的闭环验证
- 关键结果：`tdd-crud-task` 最终状态更新为 `done`
## 2. JOIN/GROUP 脚本目标与结果
- 脚本：`docs/learning/sql/04_join_and_group_practice.sql`
- 目标：验证任务与上传记录的关联统计
- 关键结果：`tdd-join-task` 的 `upload_count = 2`
## 3. 易错点
- 忘记 `WHERE`：可能误更新/误删除全表
- 外键约束触发：插入子表前必须先有父表任务
- 聚合字段遗漏：`GROUP BY` 时需包含非聚合列
- 测试数据污染：每次测试后要清理临时数据
## 4. 本任务结论
- 已能通过 SQL 脚本完成基础 CRUD 和 JOIN/GROUP 聚合
- 已通过行为测试验证结果正确性（非文件存在性测试）