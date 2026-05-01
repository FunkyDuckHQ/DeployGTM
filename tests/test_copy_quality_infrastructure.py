import json
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path


QUALITY_DOC_PATH = Path("docs/copy-quality-standard.md")
RUBRIC_PATH = Path("templates/copy-quality-rubric.json")
PACKET_SCHEMA_PATH = Path("templates/copy-packet.schema.json")
GOOD_PACKET_PATH = Path("examples/copy/qa-scored-copy.json")

validate_copy_module = SourceFileLoader(
    "validate_copy_packet",
    str(Path("3_operations/scripts/validate_copy_packet.py")),
).load_module()


class CopyQualityInfrastructureTest(unittest.TestCase):
    def test_quality_standard_defines_thresholds_and_hard_fails(self) -> None:
        content = QUALITY_DOC_PATH.read_text(encoding="utf-8")
        for phrase in [
            "Entity correctness",
            "Source-grounded specificity",
            "`pass`: 85-100",
            "Hard Fail Conditions",
            "Do not trust final copy because it \"sounds good.\"",
        ]:
            self.assertIn(phrase, content)

    def test_rubric_sums_to_100_and_has_fail_rules(self) -> None:
        rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
        total = sum(dimension["max_points"] for dimension in rubric["dimensions"])
        self.assertEqual(total, 100)
        self.assertEqual(rubric["pass_threshold"], 85)
        self.assertIn("unsupported_factual_claim", rubric["hard_fail_rules"])
        self.assertIn("at DeployGTM", rubric["banned_phrases"])

    def test_copy_packet_schema_requires_core_output_fields(self) -> None:
        schema = json.loads(PACKET_SCHEMA_PATH.read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertTrue(
            {
                "copy_packet_id",
                "client_id",
                "workflow_name",
                "target_company",
                "context_bundle_ref",
                "message_strategy",
                "emails",
                "qa_result",
                "source_trace",
            }.issubset(required)
        )
        email_required = set(schema["properties"]["emails"]["items"]["required"])
        self.assertTrue({"subject", "body", "cta", "claims_used", "source_refs", "qa_status"}.issubset(email_required))

    def test_good_copy_packet_passes_validator(self) -> None:
        result = validate_copy_module.validate_copy_packet(GOOD_PACKET_PATH, RUBRIC_PATH)
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(result.score, 91)

    def test_banned_phrase_fails_validator(self) -> None:
        packet = json.loads(GOOD_PACKET_PATH.read_text(encoding="utf-8"))
        packet["copy_packet_id"] = "copy_bad_phrase"
        packet["emails"][0]["subject"] = "Quick question"

        temp_path = Path("clients/peregrine_space/copy/tmp_bad_phrase_packet.json")
        try:
            temp_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
            result = validate_copy_module.validate_copy_packet(temp_path, RUBRIC_PATH)
            self.assertFalse(result.valid)
            self.assertTrue(any("banned phrase" in error for error in result.errors))
        finally:
            temp_path.unlink(missing_ok=True)

    def test_low_score_fails_validator(self) -> None:
        packet = json.loads(GOOD_PACKET_PATH.read_text(encoding="utf-8"))
        packet["copy_packet_id"] = "copy_low_score"
        packet["qa_result"]["total_score"] = 72
        packet["qa_result"]["decision"] = "rewrite"

        temp_path = Path("clients/peregrine_space/copy/tmp_low_score_packet.json")
        try:
            temp_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
            result = validate_copy_module.validate_copy_packet(temp_path, RUBRIC_PATH)
            self.assertFalse(result.valid)
            self.assertTrue(any("below pass threshold" in error for error in result.errors))
            self.assertTrue(any("decision must be pass" in error for error in result.errors))
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
