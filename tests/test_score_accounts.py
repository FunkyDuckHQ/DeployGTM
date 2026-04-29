import unittest
from datetime import date
from importlib.machinery import SourceFileLoader
from pathlib import Path


score_module = SourceFileLoader(
    "score_accounts", str(Path("3_operations/scripts/score_accounts.py"))
).load_module()


class ScoreAccountsTest(unittest.TestCase):
    def test_decayed_strength_half_life(self) -> None:
        observed_at = date(2026, 1, 1)
        as_of = date(2026, 1, 31)
        self.assertEqual(round(score_module.decayed_strength(100, observed_at, 30, as_of), 2), 50.0)

    def test_score_accounts_outputs_routes(self) -> None:
        output = score_module.score_accounts(
            Path("examples/peregrine/accounts.json"),
            Path("examples/peregrine/signal_definitions.json"),
            date(2026, 4, 29),
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


if __name__ == "__main__":
    unittest.main()
