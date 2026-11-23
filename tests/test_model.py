import unittest

from srml_analyzer.model import build_model
from tests.test_core_tables import sample


class ModelTests(unittest.TestCase):
    def test_builds_cross_table_summary(self):
        result = build_model(sample())
        self.assertEqual(result["format"], "il2cpp-v39-model")
        self.assertEqual(result["counts"]["types"], 1)
        self.assertEqual(result["counts"]["methods"], 1)
        self.assertEqual(result["validation"]["errors"], [])
        self.assertEqual(result["types"][0]["full_name"], "System.Thing")


if __name__ == "__main__":
    unittest.main()
