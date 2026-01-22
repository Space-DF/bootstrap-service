import json
import logging

import pika
from django.conf import settings

logger = logging.getLogger(__name__)


class EventPublisher:
    """Publishes organization lifecycle events to RabbitMQ"""

    def __init__(self):
        self.rabbitmq_url = settings.RABBITMQ_URL
        self.events_exchange = settings.ORG_EVENTS_EXCHANGE
        self.transformer_queue_name = settings.ORG_TRANSFORMER_QUEUE
        self.broker_bridge_queue_name = settings.ORG_BROKER_BRIDGE_QUEUE
        self.console_queue_name = getattr(
            settings, "ORG_CONSOLE_QUEUE", "console.org.discovery.queue"
        )
        self.discovery_routing_key = getattr(
            settings, "ORG_DISCOVERY_ROUTING_KEY", "org.discovery.request"
        )
        self.events_routing_key = settings.ORG_EVENTS_ROUTING_KEY
        self._listener_thread = None

    def setup_org_events(self):
        """
        Create events queue for Transformer and Broker Bridge services
        """
        try:
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            channel = connection.channel()

            # Declare exchange
            channel.exchange_declare(
                exchange=self.events_exchange, exchange_type="topic", durable=True
            )

            channel.queue_declare(
                self.transformer_queue_name, False, True, False, False, None
            )
            channel.queue_declare(
                self.broker_bridge_queue_name, False, True, False, False, None
            )
            channel.queue_declare(
                self.console_queue_name, False, True, False, False, None
            )

            channel.queue_bind(
                exchange=self.events_exchange,
                queue=self.transformer_queue_name,
                routing_key="org.*",
            )

            channel.queue_bind(
                exchange=self.events_exchange,
                queue=self.broker_bridge_queue_name,
                routing_key="org.*",
            )
            channel.queue_bind(
                exchange=self.events_exchange,
                queue=self.console_queue_name,
                routing_key=self.discovery_routing_key,
            )

            logger.info(
                f"Connected to RabbitMQ and declared exchange: {self.events_exchange}"
            )
            logger.info(f"Declared queues: {self.events_exchange}")
            return connection, channel

        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.AMQPChannelError,
            ConnectionError,
        ) as e:  # noqa: B014
            logger.error(f"Failed to create event connection: {e}")
            return None, None
        except Exception as e:  # noqa: B036
            logger.error(f"Failed to create event connection: {e}")
            return None, None

    def publish_event(
        self, event_type: str, event_id: str, timestamp: str, payload: dict
    ) -> bool:
        """
        Publish event to RabbitMQ

        Args:
            event_type: Event type (e.g., 'org.created', 'org.deleted')
            event_id: Unique event identifier
            timestamp: Event timestamp
            payload: Event payload

        Returns:
            True if successful
        """
        try:
            # Connect to RabbitMQ
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            channel = connection.channel()

            # Declare exchange
            channel.exchange_declare(
                exchange=self.events_exchange, exchange_type="topic", durable=True
            )

            # Publish event
            event_id = event_id
            event_timestamp = timestamp

            # Initialize envelope
            envelope = {
                "event_id": event_id,
                "event_type": event_type,
                "timestamp": event_timestamp,
                "payload": payload,
            }

            channel.basic_publish(
                exchange=self.events_exchange,
                routing_key=event_type,
                body=json.dumps(envelope),
                properties=pika.BasicProperties(
                    content_type="application/json", delivery_mode=2
                ),
            )

            logger.info(f"Published event: {event_type} to {self.events_exchange}")

            connection.close()
            return True

        except (
            pika.exceptions.AMQPConnectionError,
            pika.exceptions.AMQPChannelError,
            ConnectionError,
        ) as e:  # noqa: B014
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False
        except Exception as e:  # noqa: B036
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False


def publish_org_event(
    event_type: str, event_id: str, timestamp: str, payload: dict
) -> bool:
    """
    Convenience function to publish organization events

    Args:
        event_type: 'org.created' or 'org.deleted'
        payload: Event data
    """
    publisher = EventPublisher()
    return publisher.publish_event(event_type, event_id, timestamp, payload)
