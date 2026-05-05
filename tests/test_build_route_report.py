import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


report_module = SourceFileLoader(
    "build_route_report", str(Path("3_operations/scripts/build_route_report.py"))
).load_module()


class BuildRouteReportTest(unittest.TestCase):
    def test_report_includes_routes_and_next_actions(self) -> None:
        score_path = Path("clients/peregrine_space/outputs/score_snapshots.json")
        score_data = report_module.load_json(score_path)
        report = report_module.build_report(score_data, score_path)

        self.assertIn("Xona Space Systems", report)
        self.assertIn("Enrich + campaign test", report)
        self.assertIn("Next action", report)
        self.assertIn("clients/peregrine_space/outputs/score_snapshots.json", report)

    def test_report_understands_flashpoint_custom_routes(self) -> None:
        score_path = Path("clients/flashpoint/outputs/score_snapshots.json")
        score_data = report_module.load_json(score_path)
        report = report_module.build_report(score_data, score_path)

        self.assertIn("Monitor for signal", report)
        self.assertIn("research/watch mode", report)
        self.assertNotIn("Next action: Exclude from current motion.", report)


if __name__ == "__main__":
    unittest.main()
