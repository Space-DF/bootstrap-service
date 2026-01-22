import logging

logger = logging.getLogger(__name__)


def check_tenant_exists(provisioner, org_slug):
    exchange_name = f"{org_slug}.exchange"

    try:
        vhosts = provisioner.list_vhosts()
        for vhost in vhosts:
            if vhost == "/":
                continue

            encoded_vhost = provisioner._encode(vhost)
            encoded_exchange = provisioner._encode(exchange_name)
            response = provisioner.session.get(
                f"{provisioner.api_url}/api/exchanges/{encoded_vhost}/{encoded_exchange}"
            )
            if response.status_code == 200:
                logger.info(f"Found existing tenant '{org_slug}' in vhost '{vhost}'")
                return {
                    "exists": True,
                    "vhost": vhost,
                    "amqp_url": provisioner.build_tenant_amqp_url(vhost),
                    "exchange": exchange_name,
                    "transformer_queue": f"{org_slug}.transformer.queue",
                    "transformed_queue": f"{org_slug}.transformed.data.queue",
                }

        logger.info(f"Tenant '{org_slug}' does not exist")
        return False
    except (ConnectionError, TimeoutError, OSError) as e:
        logger.warning(f"Error checking tenant existence for '{org_slug}': {e}")
        return False
    except Exception as e:
        logger.warning(f"Error checking tenant existence for '{org_slug}': {e}")
        return False
