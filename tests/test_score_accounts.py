import unittest
from datetime import date
from importlib.machinery import SourceFileLoader
from pathlib import Path
from shutil import rmtree


score_module = SourceFileLoader(
    "score_accounts", str(Path("3_operations/scripts/score_accounts.py"))
).load_module()
bootstrap_module = SourceFileLoader(
    "bootstrap_client", str(Path("3_operations/scripts/bootstrap_client.py"))
).load_module()


class ScoreAccountsTest(unittest.TestCase):
    def test_decayed_strength_half_life(self) -> None:
        observed_at = date(2026, 1, 1)
        as_of = date(2026, 1, 31)
        self.assertEqual(round(score_module.decayed_strength(100, observed_at, 30, as_of), 2), 50.0)

    def test_score_accounts_outputs_routes(self) -> None:
        output = score_module.score_accounts(
            Path("clients/peregrine_space/inputs/accounts.json"),
            Path("clients/peregrine_space/config/signal_definitions.json"),
            date(2026, 4, 29),
            Path("clients/peregrine_space/config/scoring.json"),
        )
        snapshots = {item["account_id"]: item for item in output["score_snapshots"]}

        self.assertGreaterEqual(snapshots["acc_xona"]["icp_score"], 80)
        self.assertIn(
            snapshots["acc_xona"]["recommended_route"],
            {
                "enrich_selectively_or_monitor",
                "enrich_and_campaign_test",
                "manual_sales_review_and_enrich",
            },
        )
        self.assertIn(snapshots["acc_generic_prime"]["recommended_route"], {"hold_or_monitor", "exclude"})

    def test_scoring_config_changes_score_output(self) -> None:
        accounts = Path("clients/peregrine_space/inputs/accounts.json")
        signals = Path("clients/peregrine_space/config/signal_definitions.json")
        scoring = Path("clients/peregrine_space/config/scoring.json")
        original = score_module.score_accounts(accounts, signals, date(2026, 4, 29), scoring)
        original_xona = {item["account_id"]: item for item in original["score_snapshots"]}["acc_xona"]

        changed_scoring = Path("tests/tmp_scoring.json")
        config = score_module.load_json(scoring)
        config["icp_components"]["evidence_confidence"] = 0
        try:
            score_module.write_json(changed_scoring, config)
            changed = score_module.score_accounts(accounts, signals, date(2026, 4, 29), changed_scoring)
            changed_xona = {item["account_id"]: item for item in changed["score_snapshots"]}["acc_xona"]
        finally:
            if changed_scoring.exists():
                changed_scoring.unlink()

        self.assertLess(changed_xona["icp_score"], original_xona["icp_score"])

    def test_second_client_scores_with_same_engine(self) -> None:
        output = score_module.score_accounts(
            Path("clients/example_b2b_saas/inputs/accounts.json"),
            Path("clients/example_b2b_saas/config/signal_definitions.json"),
            date(2026, 4, 30),
            Path("clients/example_b2b_saas/config/scoring.json"),
        )
        snapshots = {item["account_id"]: item for item in output["score_snapshots"]}

        self.assertEqual(output["client_id"], "example_b2b_saas")
        self.assertIn("acc_northstar_crm", snapshots)
        self.assertGreater(snapshots["acc_northstar_crm"]["urgency_score"], 40)
        self.assertNotEqual(
            snapshots["acc_northstar_crm"]["component_scores"],
            snapshots["acc_flatfile_ops"]["component_scores"],
        )

    def test_client_workspace_validation_catches_missing_files(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing account input"):
            score_module.validate_client_workspace("missing_client_for_test")

    def test_bootstrap_client_creates_workspace_from_template(self) -> None:
        clients_root = Path("tests/tmp_clients")
        client_id = "bootstrap_demo"
        if clients_root.exists():
            rmtree(clients_root)
        try:
            created = bootstrap_module.bootstrap_client(client_id, clients_root=clients_root)
            self.assertTrue(created)
            self.assertTrue((clients_root / client_id / "config" / "scoring.json").exists())
            scoring = score_module.load_json(clients_root / client_id / "config" / "scoring.json")
            self.assertEqual(scoring["client_id"], client_id)
        finally:
            if clients_root.exists():
                rmtree(clients_root)


if __name__ == "__main__":
    unittest.main()
