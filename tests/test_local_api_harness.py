import os
import unittest
from unittest.mock import Mock, patch

from scripts.local_api_harness import (
    crm_read_test,
    crm_upsert_company_test,
    one_second_read_test,
    validate_env,
)


class LocalApiHarnessTests(unittest.TestCase):
    def setUp(self):
        os.environ["CRM_PROVIDER"] = "hubspot"
        os.environ["HUBSPOT_ACCESS_TOKEN"] = "test-token"

    @patch("scripts.local_api_harness.requests.get")
    def test_crm_read_hubspot_pass(self, mock_get):
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {"results": []}
        mock_get.return_value = mock_resp

        result = crm_read_test()
        self.assertTrue(result.ok)

    def test_crm_upsert_skips_without_write_flag(self):
        os.environ.pop("LOCAL_API_ALLOW_WRITE", None)
        result = crm_upsert_company_test("example.com", "Test Co")
        self.assertFalse(result.ok)
        self.assertIn("Skipped", result.detail)

    def test_validate_env_missing_hubspot(self):
        os.environ.pop("HUBSPOT_ACCESS_TOKEN", None)
        result = validate_env()
        self.assertFalse(result.ok)
        self.assertIn("HUBSPOT_ACCESS_TOKEN", result.detail)

    @patch("scripts.local_api_harness.requests.get")
    def test_one_second_read_pass(self, mock_get):
        mock_resp = Mock(status_code=200, text="ok")
        mock_get.return_value = mock_resp

        result = one_second_read_test()
        self.assertTrue(result.ok)

    @patch("scripts.local_api_harness.requests.get")
    def test_crm_read_generic_pass(self, mock_get):
        os.environ["CRM_PROVIDER"] = "generic"
        os.environ["CRM_BASE_URL"] = "https://crm.example.com/api"
        mock_resp = Mock(status_code=200)
        mock_resp.json.return_value = {"data": []}
        mock_get.return_value = mock_resp

        result = crm_read_test()
        self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
