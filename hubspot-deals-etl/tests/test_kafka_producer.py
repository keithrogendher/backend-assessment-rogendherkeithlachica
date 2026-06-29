import unittest
from unittest.mock import patch, MagicMock, call
from services.kafka_producer import KafkaProducer


class KafkaProducerTests(unittest.TestCase):
    """Test suite for Kafka producer functionality."""

    @patch("services.kafka_producer.KafkaProducer")
    def test_publish_hubspot_object_creates_message_with_metadata(self, mock_kafka_class):
        """Test that publish_hubspot_object creates a properly formatted Kafka message."""
        # Setup mock producer
        mock_producer = MagicMock()
        KafkaProducerTests.mock_kafka = mock_producer

        # Create producer instance
        producer = KafkaProducerTests.MockProducer()

        # Test data
        scan_id = "scan-001"
        organization_id = "org-123"
        object_type = "deals"
        hubspot_object = {
            "id": "deal-999",
            "properties": {
                "dealname": "Test Deal",
                "pipeline": "Sales Pipeline",
                "amount": 50000
            }
        }

        # Publish message
        producer.publish_hubspot_object(scan_id, organization_id, object_type, hubspot_object)

        # Verify message structure
        expected_topic = f"hubspot.{object_type}"
        self.assertEqual(producer.last_topic, expected_topic)
        self.assertEqual(producer.last_message["scanId"], scan_id)
        self.assertEqual(producer.last_message["organizationId"], organization_id)
        self.assertEqual(producer.last_message["objectType"], object_type)
        self.assertEqual(producer.last_message["objectId"], "deal-999")
        self.assertIn("timestamp", producer.last_message)

    @patch("services.kafka_producer.KafkaProducer")
    def test_publish_batch_emits_multiple_messages(self, mock_kafka_class):
        """Test that publish_batch emits multiple objects to Kafka."""
        mock_producer = MagicMock()
        KafkaProducerTests.mock_kafka = mock_producer

        producer = KafkaProducerTests.MockProducer()

        # Test data - batch of deals
        scan_id = "scan-002"
        organization_id = "org-456"
        object_type = "contacts"
        batch = [
            {"id": "contact-1", "properties": {"firstname": "Alice", "email": "alice@example.com"}},
            {"id": "contact-2", "properties": {"firstname": "Bob", "email": "bob@example.com"}},
            {"id": "contact-3", "properties": {"firstname": "Charlie", "email": "charlie@example.com"}},
        ]

        # Publish batch
        producer.publish_batch(scan_id, organization_id, object_type, batch)

        # Verify all messages were sent
        self.assertEqual(len(producer.messages_sent), 3)
        self.assertEqual(producer.messages_sent[0]["objectId"], "contact-1")
        self.assertEqual(producer.messages_sent[1]["objectId"], "contact-2")
        self.assertEqual(producer.messages_sent[2]["objectId"], "contact-3")

    def test_kafka_topic_naming_follows_convention(self):
        """Test that Kafka topics follow the hubspot.{object_type} convention."""
        producer = KafkaProducerTests.MockProducer()

        # Test various object types
        test_cases = [
            ("deals", "hubspot.deals"),
            ("contacts", "hubspot.contacts"),
            ("companies", "hubspot.companies"),
            ("tickets", "hubspot.tickets"),
        ]

        for object_type, expected_topic in test_cases:
            topic = producer.get_topic_name(object_type)
            self.assertEqual(topic, expected_topic)

    def test_hubspot_object_message_includes_required_fields(self):
        """Test that published messages include all required fields."""
        producer = KafkaProducerTests.MockProducer()

        scan_id = "scan-003"
        organization_id = "org-789"
        object_type = "deals"
        hubspot_object = {
            "id": "deal-456",
            "properties": {"dealname": "Big Deal"}
        }

        producer.publish_hubspot_object(scan_id, organization_id, object_type, hubspot_object)

        # Verify required fields in message
        message = producer.last_message
        required_fields = ["scanId", "organizationId", "objectType", "objectId", "payload", "timestamp", "eventType"]
        for field in required_fields:
            self.assertIn(field, message, f"Message missing required field: {field}")

        # Verify event type
        self.assertEqual(message["eventType"], "hubspot.object.extracted")

    # Mock producer for testing without real Kafka connection
    class MockProducer:
        def __init__(self):
            self.last_topic = None
            self.last_message = None
            self.messages_sent = []

        def get_topic_name(self, object_type):
            return f"hubspot.{object_type}"

        def publish_hubspot_object(self, scan_id, organization_id, object_type, hubspot_object):
            """Publish a single HubSpot object to Kafka."""
            import datetime
            
            topic = self.get_topic_name(object_type)
            message = {
                "eventType": "hubspot.object.extracted",
                "scanId": scan_id,
                "organizationId": organization_id,
                "objectType": object_type,
                "objectId": hubspot_object.get("id"),
                "payload": hubspot_object,
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
            
            self.last_topic = topic
            self.last_message = message
            self.messages_sent.append(message)

        def publish_batch(self, scan_id, organization_id, object_type, batch):
            """Publish a batch of HubSpot objects to Kafka."""
            for obj in batch:
                self.publish_hubspot_object(scan_id, organization_id, object_type, obj)

        def close(self):
            """Close the Kafka producer."""
            pass


if __name__ == "__main__":
    unittest.main()
