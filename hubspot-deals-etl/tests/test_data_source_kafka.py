import unittest
from unittest.mock import patch, MagicMock, call
from services.data_source import create_data_source


class DataSourceKafkaIntegrationTests(unittest.TestCase):
    """Test Kafka integration with data source extraction."""

    @patch("services.data_source.kafka_producer")
    @patch("services.data_source.APIService")
    def test_data_source_creates_kafka_producer(self, mock_api_service, mock_kafka):
        """Test that Kafka producer is created during data source initialization."""
        # Setup mocks
        mock_kafka.create_kafka_producer.return_value = MagicMock()
        
        # Create data source with required config
        job_config = {
            "organizationId": "org-123"
        }
        auth_config = {
            "accessToken": "token-123"
        }
        filters = {
            "objectType": "deals",
            "scan_id": "scan-001"
        }
        
        # Initialize data source
        source_list = create_data_source(job_config, auth_config, filters)
        
        # Verify Kafka producer was created
        mock_kafka.create_kafka_producer.assert_called_once()
        self.assertIsNotNone(source_list)

    @patch("services.data_source.kafka_producer")
    def test_kafka_producer_disabled_when_env_disabled(self, mock_kafka):
        """Test that Kafka producer can be disabled via environment variable."""
        # Setup mock to return None (disabled)
        mock_kafka.create_kafka_producer.return_value = None
        
        job_config = {"organizationId": "org-456"}
        auth_config = {"accessToken": "token-456"}
        filters = {"objectType": "contacts", "scan_id": "scan-002"}
        
        # Create data source with disabled Kafka
        source_list = create_data_source(job_config, auth_config, filters)
        
        # Verify source was created even with no Kafka
        self.assertIsNotNone(source_list)


if __name__ == "__main__":
    unittest.main()
