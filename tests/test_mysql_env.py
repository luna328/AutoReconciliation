import os
import unittest
class TestMySqlEnv(unittest.TestCase):
    def test_env_example_exists(self):
        self.assertTrue(os.path.exists(".env.example"))
    def test_database_url_key_documented(self):
        with open(".env.example", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("DATABASE_URL=", content)