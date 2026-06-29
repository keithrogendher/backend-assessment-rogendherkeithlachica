import unittest
from unittest.mock import patch

from flask import Flask

from api.routes import create_api


class CleanupRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        api = create_api()
        api.init_app(self.app)

    @patch("api.routes.ExtractionService.cleanup_old_scans")
    def test_cleanup_endpoint_returns_deleted_count(self, mock_cleanup):
        mock_cleanup.return_value = 3

        with self.app.test_client() as client:
            response = client.post(
                "/api/maintenance/cleanup",
                json={"daysOld": 7},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["success"])
        self.assertEqual(payload["data"]["cleanedCount"], 3)


if __name__ == "__main__":
    unittest.main()
