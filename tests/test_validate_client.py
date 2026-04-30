import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path
from shutil import copytree, rmtree


validate_module = SourceFileLoader(
    "validate_client", str(Path("3_operations/scripts/validate_client.py"))
).load_module()


class ValidateClientTest(unittest.TestCase):
    def test_valid_client_returns_structured_result(self) -> None:
        result = validate_module.validate_client("peregrine_space")

        self.assertTrue(result.valid)
        self.assertEqual(result.client_id, "peregrine_space")
        self.assertGreaterEqual(len(result.files_checked), 5)
        self.assertEqual(result.errors, [])

    def test_validation_report_writes_to_runs(self) -> None:
        result = validate_module.validate_client("example_b2b_saas")
        path = validate_module.write_validation_report(result, run_id="test-validation")
        try:
            self.assertTrue(path.exists())
            self.assertEqual(path.name, "test-validation.validation.json")
            self.assertIn('"valid": true', path.read_text(encoding="utf-8"))
        finally:
            if path.exists():
                path.unlink()

    def test_wrong_client_id_is_reported(self) -> None:
        clients_root = Path("tests/tmp_validation_clients")
        client_id = "bad_client_id"
        target = clients_root / client_id
        if clients_root.exists():
            rmtree(clients_root)
        try:
            copytree(Path("clients/_template"), target)
            scoring_path = target / "config" / "scoring.json"
            content = scoring_path.read_text(encoding="utf-8").replace("__CLIENT_ID__", "other_client")
            scoring_path.write_text(content, encoding="utf-8")

            result = validate_module.validate_client(client_id, clients_root)
            self.assertFalse(result.valid)
            self.assertTrue(any("scoring.json client_id other_client does not match bad_client_id" in error for error in result.errors))
        finally:
            if clients_root.exists():
                rmtree(clients_root)

    def test_bad_account_shape_is_reported(self) -> None:
        clients_root = Path("tests/tmp_validation_clients")
        client_id = "bad_account_shape"
        target = clients_root / client_id
        if clients_root.exists():
            rmtree(clients_root)
        try:
            copytree(Path("clients/_template"), target)
            for path in target.rglob("*.json"):
                path.write_text(path.read_text(encoding="utf-8").replace("__CLIENT_ID__", client_id), encoding="utf-8")
            accounts_path = target / "inputs" / "accounts.json"
            accounts_path.write_text(
                '{"client_id":"bad_account_shape","accounts":[{"account_id":"acc_missing_name"}]}',
                encoding="utf-8",
            )

            result = validate_module.validate_client(client_id, clients_root)
            self.assertFalse(result.valid)
            self.assertTrue(any("accounts[0] missing required fields: company_name" in error for error in result.errors))
        finally:
            if clients_root.exists():
                rmtree(clients_root)


if __name__ == "__main__":
    unittest.main()
