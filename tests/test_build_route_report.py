import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


report_module = SourceFileLoader(
    "build_route_report", str(Path("3_operations/scripts/build_route_report.py"))
).load_module()


class BuildRouteReportTest(unittest.TestCase):
    def test_report_includes_routes_and_next_actions(self) -> None:
        score_data = report_module.load_json(Path("3_operations/outputs/peregrine_score_snapshots.json"))
        report = report_module.build_report(score_data)

        self.assertIn("Xona Space Systems", report)
        self.assertIn("Enrich + campaign test", report)
        self.assertIn("Next action", report)
        self.assertIn("Peregrine Space working brief", report)


if __name__ == "__main__":
    unittest.main()
