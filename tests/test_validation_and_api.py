import os
import unittest

import pandas as pd

os.environ.setdefault("DATABASE_URL", "sqlite:///test_reconciliation.db")

from app import (
    ReconcileResult,
    ReconcileTask,
    ValidationError,
    app,
    db,
    standardize_vendor_data,
)


class TestValidationAndApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        with app.app_context():
            db.create_all()

    def setUp(self):
        self.client = app.test_client()
        with app.app_context():
            ReconcileResult.query.delete()
            ReconcileTask.query.delete()
            db.session.commit()

    def test_create_task_and_recent_tasks(self):
        resp = self.client.post("/api/task/create", json={})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        task_id = data["task_id"]

        recent_resp = self.client.get("/api/tasks/recent?limit=5")
        self.assertEqual(recent_resp.status_code, 200)
        recent = recent_resp.get_json()
        self.assertTrue(any(t["task_id"] == task_id for t in recent["tasks"]))

    def test_export_requires_existing_result(self):
        with app.app_context():
            task = ReconcileTask(id="task-export-test", status="created")
            db.session.add(task)
            db.session.commit()

        resp = self.client.post("/api/export", json={"task_id": "task-export-test"})
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["code"], "RESULT_NOT_FOUND")

    def test_vendor_qty_strict_integer_validation(self):
        mapping = {
            "po_no": "订单号码",
            "item_code": "物料编码",
            "item_name": "品名",
            "qty": "数量",
            "unit_price": "单价",
            "amount": "金额",
        }

        bad_values = [10.5, "abc", ""]
        for value in bad_values:
            with self.subTest(value=value):
                df = pd.DataFrame(
                    {
                        "订单号码": ["PO001"],
                        "物料编码": ["ITEM001"],
                        "品名": ["X"],
                        "数量": [value],
                        "单价": [1.2],
                        "金额": [12.0],
                    }
                )
                with self.assertRaises(ValidationError) as ctx:
                    standardize_vendor_data(df, mapping)
                self.assertEqual(ctx.exception.code, "INVALID_QTY")


if __name__ == "__main__":
    unittest.main()
