"""
Kafka Producer for HubSpot extraction service.

Emits extracted HubSpot objects to Kafka topics for real-time streaming
and downstream processing. Uses confluent-kafka client with configurable
topic routing and message serialization.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from loki_logger import get_logger, log_business_event


class KafkaProducer:
    """
    Kafka producer for HubSpot extraction events.
    
    Topics:
    - hubspot.deals: Extracted Deal objects
    - hubspot.contacts: Extracted Contact objects
    - hubspot.companies: Extracted Company objects
    - hubspot.tickets: Extracted Ticket objects
    - hubspot.extraction.status: Extraction status events (started, completed, failed)
    
    Message format (example):
    {
        "eventType": "hubspot.object.extracted",
        "scanId": "scan-001",
        "organizationId": "org-123",
        "objectType": "deals",
        "objectId": "deal-999",
        "payload": { ... HubSpot object properties ... },
        "timestamp": "2026-06-29T14:30:45.123456",
        "sourceService": "hubspot-extraction-service"
    }
    """
    
    def __init__(self, 
                 bootstrap_servers: Optional[str] = None,
                 topic_prefix: str = "hubspot",
                 enable_ssl: bool = False):
        """
        Initialize Kafka producer.
        
        Args:
            bootstrap_servers: Kafka broker addresses (comma-separated)
                             Defaults to KAFKA_BROKERS env var or "localhost:9092"
            topic_prefix: Prefix for all topics (default: "hubspot")
            enable_ssl: Whether to use SSL for Kafka connection
        """
        import os
        from confluent_kafka import Producer
        
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BROKERS", "localhost:9092")
        self.topic_prefix = topic_prefix
        self.logger = get_logger(__name__)
        
        # Kafka producer config
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": "hubspot-extraction-service",
            "enable.idempotence": True,  # Exactly-once semantics
            "linger.ms": 100,            # Batch messages for 100ms
            "compression.type": "snappy",  # Compress messages
        }
        
        if enable_ssl:
            config.update({
                "security.protocol": "ssl",
                "ssl.ca.location": os.getenv("KAFKA_CA_CERT", "/etc/kafka/certs/ca.pem"),
                "ssl.certificate.location": os.getenv("KAFKA_CLIENT_CERT", "/etc/kafka/certs/client.pem"),
                "ssl.key.location": os.getenv("KAFKA_CLIENT_KEY", "/etc/kafka/certs/client.key"),
            })
        
        try:
            self.producer = Producer(config)
            self.logger.info(f"Kafka producer initialized: {self.bootstrap_servers}")
            log_business_event("kafka_producer_initialized", {
                "bootstrap_servers": self.bootstrap_servers,
                "topic_prefix": topic_prefix,
                "ssl_enabled": enable_ssl
            })
        except Exception as e:
            self.logger.error(f"Failed to initialize Kafka producer: {e}")
            log_business_event("kafka_producer_init_failed", {
                "error": str(e),
                "bootstrap_servers": self.bootstrap_servers
            })
            raise
    
    def get_topic_name(self, object_type: str) -> str:
        """Get Kafka topic name for object type."""
        return f"{self.topic_prefix}.{object_type.lower()}"
    
    def publish_hubspot_object(self, 
                              scan_id: str,
                              organization_id: str,
                              object_type: str,
                              hubspot_object: Dict[str, Any]) -> bool:
        """
        Publish a single extracted HubSpot object to Kafka.
        
        Args:
            scan_id: Unique scan identifier
            organization_id: Organization UUID
            object_type: HubSpot object type (deals, contacts, companies, etc.)
            hubspot_object: The extracted HubSpot object with id and properties
        
        Returns:
            bool: True if message was queued successfully
        """
        try:
            topic = self.get_topic_name(object_type)
            
            # Create event message
            message = {
                "eventType": "hubspot.object.extracted",
                "scanId": scan_id,
                "organizationId": organization_id,
                "objectType": object_type,
                "objectId": hubspot_object.get("id"),
                "payload": hubspot_object,
                "timestamp": datetime.utcnow().isoformat(),
                "sourceService": "hubspot-extraction-service"
            }
            
            # Serialize to JSON
            message_json = json.dumps(message)
            
            # Publish to Kafka
            self.producer.produce(
                topic=topic,
                key=hubspot_object.get("id", "").encode("utf-8"),
                value=message_json.encode("utf-8"),
                callback=self._delivery_report
            )
            
            self.logger.debug(f"Published object {hubspot_object.get('id')} to {topic}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to publish HubSpot object: {e}")
            log_business_event("kafka_publish_failed", {
                "error": str(e),
                "scan_id": scan_id,
                "object_type": object_type,
                "object_id": hubspot_object.get("id")
            })
            return False
    
    def publish_batch(self,
                     scan_id: str,
                     organization_id: str,
                     object_type: str,
                     batch: List[Dict[str, Any]],
                     callback=None) -> int:
        """
        Publish a batch of HubSpot objects to Kafka.
        
        Args:
            scan_id: Unique scan identifier
            organization_id: Organization UUID
            object_type: HubSpot object type
            batch: List of extracted HubSpot objects
            callback: Optional callback function for batch completion
        
        Returns:
            int: Number of messages successfully queued
        """
        count = 0
        for obj in batch:
            if self.publish_hubspot_object(scan_id, organization_id, object_type, obj):
                count += 1
        
        self.logger.info(f"Published {count}/{len(batch)} objects from batch")
        
        if callback:
            try:
                callback(count, len(batch))
            except Exception as e:
                self.logger.warning(f"Batch callback failed: {e}")
        
        return count
    
    def publish_extraction_event(self,
                                scan_id: str,
                                organization_id: str,
                                event_type: str,
                                metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Publish extraction lifecycle event (started, completed, failed, paused).
        
        Args:
            scan_id: Unique scan identifier
            organization_id: Organization UUID
            event_type: Event type (started, completed, failed, paused, resumed)
            metadata: Optional metadata for the event
        
        Returns:
            bool: True if message was queued successfully
        """
        try:
            topic = f"{self.topic_prefix}.extraction.status"
            
            message = {
                "eventType": f"hubspot.extraction.{event_type}",
                "scanId": scan_id,
                "organizationId": organization_id,
                "timestamp": datetime.utcnow().isoformat(),
                "sourceService": "hubspot-extraction-service",
                "metadata": metadata or {}
            }
            
            message_json = json.dumps(message)
            
            self.producer.produce(
                topic=topic,
                key=scan_id.encode("utf-8"),
                value=message_json.encode("utf-8"),
                callback=self._delivery_report
            )
            
            self.logger.info(f"Published extraction event: {event_type} for scan {scan_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to publish extraction event: {e}")
            log_business_event("kafka_event_publish_failed", {
                "error": str(e),
                "scan_id": scan_id,
                "event_type": event_type
            })
            return False
    
    def _delivery_report(self, err, msg):
        """Kafka delivery report callback for debugging."""
        if err is not None:
            self.logger.warning(f"Message delivery failed: {err}")
            log_business_event("kafka_delivery_failed", {
                "error": str(err),
                "topic": msg.topic() if msg else "unknown"
            })
        else:
            self.logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    
    def flush(self, timeout_ms: int = 5000) -> int:
        """
        Flush any pending messages.
        
        Args:
            timeout_ms: Timeout in milliseconds to wait for delivery
        
        Returns:
            int: Number of messages still in queue after timeout
        """
        remaining = self.producer.flush(timeout_ms)
        if remaining > 0:
            self.logger.warning(f"{remaining} messages still pending in queue")
        return remaining
    
    def close(self):
        """Close the Kafka producer and flush pending messages."""
        try:
            self.flush(timeout_ms=10000)
            self.logger.info("Kafka producer closed")
        except Exception as e:
            self.logger.error(f"Error closing Kafka producer: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Factory function for easier instantiation
def create_kafka_producer(topic_prefix: str = "hubspot") -> Optional[KafkaProducer]:
    """
    Create a Kafka producer instance.
    
    Args:
        topic_prefix: Prefix for all topics
    
    Returns:
        KafkaProducer instance or None if Kafka is disabled
    """
    import os
    
    logger = get_logger(__name__)
    
    # Allow disabling Kafka via environment variable
    if os.getenv("KAFKA_ENABLED", "true").lower() == "false":
        logger.info("Kafka producer disabled via KAFKA_ENABLED=false")
        return None
    
    try:
        return KafkaProducer(topic_prefix=topic_prefix)
    except Exception as e:
        logger.error(f"Failed to create Kafka producer: {e}")
        return None
