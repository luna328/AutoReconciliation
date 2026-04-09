import os
import unittest
import pymysql
class TestSqlCrudBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conn = pymysql.connect(
            host="127.0.0.1",
            user="recon_user",
            password="recon_pass",
            database="reconciliation",
            autocommit=True,
        )
        cls.cur = cls.conn.cursor()
    @classmethod
    def tearDownClass(cls):
        cls.cur.close()
        cls.conn.close()
    def _run_sql_file(self, path):
        self.assertTrue(os.path.exists(path), f"SQL file missing: {path}")
        with open(path, "r", encoding="utf-8") as f:
            sql_text = f.read()
        statements = [s.strip() for s in sql_text.split(";") if s.strip()]
        for stmt in statements:
            self.cur.execute(stmt)
    def test_crud_script_results(self):
        # 执行 CRUD 练习脚本
        self._run_sql_file("docs/learning/sql/03_crud_practice.sql")
        # 验证 UPDATE 后状态为 done
        self.cur.execute(
            "SELECT status FROM reconcile_task WHERE task_name='tdd-crud-task' ORDER BY id DESC LIMIT 1"
        )
        row = self.cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "done")
        # 清理
        self.cur.execute("DELETE FROM reconcile_task WHERE task_name='tdd-crud-task'")
    def test_join_group_script_results(self):
        # 执行 JOIN/GROUP 练习脚本
        self._run_sql_file("docs/learning/sql/04_join_and_group_practice.sql")
        # 验证聚合结果：该任务对应 2 条上传记录
        self.cur.execute(
            """
            SELECT COUNT(u.id)
            FROM reconcile_task t
            LEFT JOIN upload_record u ON u.task_id = t.id
            WHERE t.task_name='tdd-join-task'
            GROUP BY t.id
            ORDER BY t.id DESC
            LIMIT 1
            """
        )
        row = self.cur.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], 2)
        # 清理
        self.cur.execute("DELETE FROM reconcile_task WHERE task_name='tdd-join-task'")