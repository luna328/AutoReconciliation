import os
import unittest
class TestMySqlLearningAssets(unittest.TestCase):
    def test_learning_checklist_exists(self):
        self.assertTrue(os.path.exists("docs/learning/mysql-learning-checklist.md"))