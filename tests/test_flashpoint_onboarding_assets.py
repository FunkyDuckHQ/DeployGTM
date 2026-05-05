import json
import unittest
from datetime import date
from importlib.machinery import SourceFileLoader
from pathlib import Path


validate_module = SourceFileLoader(
    "validate_client", str(Path("3_operations/scripts/validate_client.py"))
).load_module()
score_module = SourceFileLoader(
    "score_accounts", str(Path("3_operations/scripts/score_accounts.py"))
).load_module()


class FlashpointOnboardingAssetsTest(unittest.TestCase):
    def test_flashpoint_workspace_validates(self) -> None:
        result = validate_module.validate_client("flashpoint")

        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])
        self.assertGreaterEqual(len(result.files_checked), 5)

    def test_flashpoint_signals_are_process_backed(self) -> None:
        signals = json.loads(Path("clients/flashpoint/config/signal_definitions.json").read_text(encoding="utf-8"))
        definitions = {item["signal_definition_id"]: item for item in signals["signal_definitions"]}

        expected = {
            "ai_self_serve_pressure",
            "survey_ops_or_programming_need",
            "bank_cpg_product_innovation_fit",
            "tracking_or_monitoring_recurrence",
            "rfp_differentiation_pressure",
            "research_ops_hiring_signal",
        }

        self.assertEqual(set(definitions), expected)
        for definition in definitions.values():
            self.assertTrue(definition["research_process_refs"])
            self.assertIn("bird_dog_setup_notes", definition)
            self.assertGreater(definition["urgency_weight"], 0)

    def test_flashpoint_vendor_rules_are_no_write_by_default(self) -> None:
        vendors = json.loads(Path("clients/flashpoint/config/vendors.json").read_text(encoding="utf-8"))["vendors"]

        for key in ["research_process", "company_discovery", "people_enrichment", "technographics"]:
            self.assertIn(key, vendors)

        self.assertEqual(vendors["research_process"]["status"], "reference_adopted")
        self.assertEqual(vendors["company_discovery"]["status"], "evaluate_no_write")
        self.assertIn("dry-run before spend", vendors["company_discovery"]["guardrails"])
        self.assertIn("no export until segment logic is approved", vendors["people_enrichment"]["guardrails"])

    def test_mitchell_deep_dive_documents_adoption_decision(self) -> None:
        content = Path("docs/mitchell-keller-github-deep-dive.md").read_text(encoding="utf-8")

        self.assertIn("Adopt the workflow ideas now. Do not vendor the code yet.", content)
        self.assertIn("research-process-builder", content)
        self.assertIn("ai-ark-cli", content)
        self.assertIn("discolike-cli", content)
        self.assertIn("techsight-cli", content)
        self.assertIn("Flashpoint Adoption", content)

    def test_flashpoint_gtm_workflow_is_operational_not_sdr_volume(self) -> None:
        content = Path("workflows/flashpoint-gtm-pilot.md").read_text(encoding="utf-8")

        self.assertIn("30/60/90", content)
        self.assertIn("copy packet", content)
        self.assertIn("count -> 10-record validation -> confirmation", content)
        self.assertIn("No proof asset, no scaled outreach.", content)
        self.assertIn("not a meeting-volume workflow", content)

    def test_flashpoint_seed_segments_score_with_current_engine(self) -> None:
        output = score_module.score_accounts(
            Path("clients/flashpoint/inputs/accounts.json"),
            Path("clients/flashpoint/config/signal_definitions.json"),
            date(2026, 5, 5),
            Path("clients/flashpoint/config/scoring.json"),
        )
        snapshots = {item["account_id"]: item for item in output["score_snapshots"]}

        self.assertEqual(output["client_id"], "flashpoint")
        self.assertIn("segment_bank_focused_research_agencies", snapshots)
        self.assertIn("segment_survey_programming_agencies", snapshots)
        self.assertGreaterEqual(snapshots["segment_survey_programming_agencies"]["icp_score"], 78)
        self.assertEqual(
            snapshots["segment_survey_programming_agencies"]["recommended_route"],
            "monitor_for_signal",
        )


if __name__ == "__main__":
    unittest.main()
