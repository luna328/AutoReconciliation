import unittest
import pymysql
class TestSchemaConstraints(unittest.TestCase):
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
    def test_tables_exist(self):
        self.cur.execute("SHOW TABLES")
        names = {row[0] for row in self.cur.fetchall()}
        self.assertIn("reconcile_task", names)
        self.assertIn("upload_record", names)
        self.assertIn("reconcile_result", names)
    def test_upload_record_requires_existing_task(self):
        with self.assertRaises(pymysql.err.IntegrityError):
            self.cur.execute(
                "INSERT INTO upload_record(task_id, file_type, file_name) VALUES (999999, 'left', 'x.csv')"
            )
    def test_reconcile_result_task_id_is_unique(self):
        self.cur.execute("INSERT INTO reconcile_task(task_name, status) VALUES ('uq-test', 'created')")
        self.cur.execute("SELECT LAST_INSERT_ID()")
        task_id = self.cur.fetchone()[0]
        self.cur.execute(
            "INSERT INTO reconcile_result(task_id, result_status, diff_count) VALUES (%s, 'done', 0)",
            (task_id,),
        )
        with self.assertRaises(pymysql.err.IntegrityError):
            self.cur.execute(
                "INSERT INTO reconcile_result(task_id, result_status, diff_count) VALUES (%s, 'done', 1)",
                (task_id,),
            )
    def test_delete_task_cascades_upload_record(self):
        self.cur.execute("INSERT INTO reconcile_task(task_name, status) VALUES ('cascade-test', 'created')")
        self.cur.execute("SELECT LAST_INSERT_ID()")
        task_id = self.cur.fetchone()[0]
        self.cur.execute(
            "INSERT INTO upload_record(task_id, file_type, file_name) VALUES (%s, 'left', 'a.csv')",
            (task_id,),
        )
        self.cur.execute("DELETE FROM reconcile_task WHERE id=%s", (task_id,))
        self.cur.execute("SELECT COUNT(*) FROM upload_record WHERE task_id=%s", (task_id,))
        self.assertEqual(self.cur.fetchone()[0], 0)