import json
import unittest
from pathlib import Path


WORKFLOW_PATH = Path("workflows/deploygtm-prospect-copy.md")
CONTEXT_SCHEMA_PATH = Path("templates/context-bundle.schema.json")
STRATEGY_TEMPLATE_PATH = Path("templates/message-strategy.md")
QA_TEMPLATE_PATH = Path("templates/copy-qa-checklist.md")
OUTPUT_TEMPLATE_PATH = Path("templates/copy-output.md")


class CopyWorkflowContractTest(unittest.TestCase):
    def test_workflow_doc_has_required_sections(self) -> None:
        content = WORKFLOW_PATH.read_text(encoding="utf-8")
        required_sections = [
            "## 1. Purpose",
            "## 2. Trigger Phrases",
            "## 3. Required Inputs",
            "## 4. Source Priority",
            "## 5. Workflow Stages",
            "## 6. Context Bundle Schema",
            "## 7. Message Strategy Template",
            "## 8. Octave Usage Rules",
            "## 9. Copy Output Formats",
            "## 10. Voice QA Checklist",
            "## 11. Banned Phrases",
            "## 12. Final Response Format",
        ]
        for section in required_sections:
            self.assertIn(section, content)

    def test_workflow_doc_enforces_octave_boundaries(self) -> None:
        content = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("Never let Octave be the first source of truth", content)
        self.assertIn("Do not use Octave for:", content)
        self.assertIn("entity resolution", content)
        self.assertIn("factual guessing", content)

    def test_context_bundle_schema_is_valid_json_and_requires_core_objects(self) -> None:
        schema = json.loads(CONTEXT_SCHEMA_PATH.read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertTrue(
            {
                "workflow",
                "client",
                "target_company",
                "entity_resolution",
                "canonical_sources",
                "account_person_brief",
                "message_strategy",
                "adapter_instructions",
                "qa",
                "source_trace",
            }.issubset(required)
        )
        self.assertEqual(schema["properties"]["workflow"]["properties"]["name"]["const"], "DeployGTM Prospect Copy")

    def test_templates_have_expected_operator_sections(self) -> None:
        strategy = STRATEGY_TEMPLATE_PATH.read_text(encoding="utf-8")
        qa = QA_TEMPLATE_PATH.read_text(encoding="utf-8")
        output = OUTPUT_TEMPLATE_PATH.read_text(encoding="utf-8")

        for phrase in ["Primary Hypothesis", "Pain Angle", "Claims Allowed", "Claims Blocked"]:
            self.assertIn(phrase, strategy)
        for phrase in ["Entity QA", "Context QA", "Banned Phrase Check", "Human review required"]:
            self.assertIn(phrase, qa)
        for phrase in ["Entity Resolution", "Final Recommended Copy", "QA Notes", "Source Trace"]:
            self.assertIn(phrase, output)

    def test_client_workspaces_include_copy_folder(self) -> None:
        for client_id in ["_template", "peregrine_space", "example_b2b_saas"]:
            self.assertTrue((Path("clients") / client_id / "copy").exists())


if __name__ == "__main__":
    unittest.main()
