import unittest
from unittest.mock import patch

from flask import Flask

from api.routes import create_api
from services.hubspot_api_service import APIService


class HubSpotApiServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = APIService(base_url="https://api.hubapi.com")

    @patch("services.hubspot_api_service.requests.Session.post")
    def test_search_payload_uses_cursor_and_last_modified_filter(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"id": "1", "properties": {"dealname": "Demo"}}],
            "paging": {"next": {"after": "cursor-2"}},
        }
        mock_response.headers = {}

        result = self.service.search_objects(
            access_token="token",
            object_type="deals",
            filters={"last_modified_date": "1704067200000"},
            limit=100,
            after=None,
        )

        self.assertIn("results", result)
        self.assertEqual(result["results"][0]["id"], "1")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.hubapi.com/crm/v3/objects/deals/search")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer token")
        self.assertEqual(kwargs["json"]["limit"], 100)
        self.assertEqual(kwargs["json"]["filterGroups"][0]["filters"][0]["propertyName"], "lastmodifieddate")

    @patch("services.hubspot_api_service.requests.Session.post")
    def test_get_associations_posts_batch_read_request(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "COMPLETE",
            "results": [{"from": {"id": "101"}, "to": [{"id": "55", "type": "contact_to_company"}]}],
        }
        mock_response.headers = {}

        result = self.service.get_associations(
            access_token="token",
            from_object_type="contacts",
            to_object_type="companies",
            object_ids=["101", "102"],
        )

        self.assertEqual(result["status"], "COMPLETE")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://api.hubapi.com/crm/v3/associations/contacts/companies/batch/read")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer token")
        self.assertEqual(kwargs["json"]["inputs"][0]["id"], "101")


class HubSpotKeyVerificationEndpointTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        api = create_api()
        api.init_app(self.app)

    @patch("api.routes.APIService.validate_token")
    def test_key_verify_endpoint_returns_valid_status(self, mock_validate_token):
        mock_validate_token.return_value = True

        with self.app.test_client() as client:
            response = client.get("/api/key/verify?accessToken=test-token")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["data"]["valid"])


if __name__ == "__main__":
    unittest.main()
