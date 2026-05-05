import unittest
from datetime import date
from importlib.machinery import SourceFileLoader
from pathlib import Path


score_module = SourceFileLoader(
    "score_accounts", str(Path("3_operations/scripts/score_accounts.py"))
).load_module()


class RunClientWorkflowTest(unittest.TestCase):
    def test_score_client_validates_and_writes_output(self) -> None:
        output_path = Path("clients/example_b2b_saas/outputs/test_score_snapshots.json")
        try:
            output, paths = score_module.score_client(
                "example_b2b_saas",
                date(2026, 4, 30),
                output_path=output_path,
            )
            self.assertEqual(paths.client_id, "example_b2b_saas")
            self.assertTrue(output_path.exists())
            self.assertEqual(output["client_id"], "example_b2b_saas")
            self.assertGreaterEqual(len(output["score_snapshots"]), 2)
        finally:
            if output_path.exists():
                output_path.unlink()


if __name__ == "__main__":
    unittest.main()
