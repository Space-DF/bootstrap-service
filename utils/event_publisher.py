# Copyright 2026 Digital Fortress.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import logging
import threading
import time
import uuid

import pika
from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

logger = logging.getLogger(__name__)

_listener_lock = threading.Lock()
_listener_started = False


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

    def setup_org_event(self):
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

    def start_discovery_listener(self):
        """Start background listener for discovery requests"""
        global _listener_started

        with _listener_lock:
            if _listener_started:
                return
            _listener_started = True

        threading.Thread(
            target=self._listen_for_discovery_requests,
            name="OrgDiscoveryListener",
            daemon=True,
        ).start()

        logger.info("Discovery listener started for spacedf organization")

    def _listen_for_discovery_requests(self):
        """Listen and respond to discovery requests with org.created events"""
        while True:
            connection = None
            try:
                close_old_connections()
                connection = pika.BlockingConnection(
                    pika.URLParameters(self.rabbitmq_url)
                )
                channel = connection.channel()

                # Setup discovery queue
                channel.exchange_declare(
                    exchange=self.events_exchange, exchange_type="topic", durable=True
                )
                channel.queue_declare(
                    self.console_queue_name, False, True, False, False, None
                )
                channel.queue_bind(
                    exchange=self.events_exchange,
                    queue=self.console_queue_name,
                    routing_key=self.discovery_routing_key,
                )

                channel.basic_qos(prefetch_count=1)
                channel.basic_consume(
                    queue=self.console_queue_name,
                    on_message_callback=self._handle_discovery_request,
                    auto_ack=False,
                )

                logger.info("Listening on queue '%s'", self.console_queue_name)
                channel.start_consuming()

            except Exception as e:
                logger.exception("Discovery listener error: %s", e)
                time.sleep(5)
            finally:
                close_old_connections()
                if connection and connection.is_open:
                    connection.close()

    def _handle_discovery_request(self, channel, method, _properties, body):
        """Handle discovery request and publish org.created for spacedf"""
        from common.rabitmq.rabbitmq_provisioner import RabbitMQProvisioner

        from apps.organization.models import Organization

        close_old_connections()

        try:
            request = json.loads(body.decode("utf-8"))
            reply_to = request.get("reply_to")

            org = Organization.objects.filter(slug_name="spacedf").first()
            if not org:
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return

            # Build and publish org.created
            provisioner = RabbitMQProvisioner()
            envelope = {
                "event_id": str(uuid.uuid4()),
                "event_type": "org.created",
                "timestamp": timezone.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "payload": {
                    "id": str(org.id),
                    "slug": org.slug_name,
                    "name": org.name,
                    "vhost": org.rabbitmq_vhost,
                    "amqp_url": provisioner.build_tenant_amqp_url(org.rabbitmq_vhost),
                    "exchange": f"{org.slug_name}.exchange",
                    "transformer_queue": f"{org.slug_name}.transformer.queue",
                    "transformed_queue": f"{org.slug_name}.transformed.data.queue",
                    "is_active": org.is_active,
                    "created_at": org.created_at.isoformat()
                    if hasattr(org, "created_at")
                    else None,
                    "updated_at": org.updated_at.isoformat()
                    if hasattr(org, "updated_at")
                    else None,
                },
            }

            channel.basic_publish(
                exchange="" if reply_to else self.events_exchange,
                routing_key=reply_to or "org.created",
                body=json.dumps(envelope),
                properties=pika.BasicProperties(
                    content_type="application/json", delivery_mode=2
                ),
            )

            channel.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.exception("Discovery error: %s", e)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        finally:
            close_old_connections()

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
