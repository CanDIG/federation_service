"""
Methods to handle services and peer servers
"""

import json
from flask import current_app
import authx.auth
import os
from candigv2_logging.logging import CanDIGLogger


logger = CanDIGLogger(__file__)


TYK_FEDERATION_API_ID = os.getenv("TYK_FEDERATION_API_ID")


def get_registered_servers():
    stored_servers_dict, status_code = authx.auth.get_service_store_secret("federation", key="servers")
    if status_code == 404:
        # no value was found, so this must need to be initialized
        stored_servers_dict, status_code = authx.auth.set_service_store_secret("federation", key="servers", value=json.dumps({"servers": {}}))
        return {}
    if status_code != 200:
        logger.error(f"Error in get_registered_servers: {stored_servers_dict}")
        return None
    return stored_servers_dict["servers"]


def register_server(obj):
    servers = get_registered_servers()
    new_server = obj['server']
    if servers is not None:
        # check to see if it's already here:
        found = False
        for s in servers.values():
            if json.dumps(s, sort_keys=True) == json.dumps(new_server, sort_keys=True):
                found = True
        if found:
            return None
        servers[new_server['id']] = obj

    if 'testing' in obj['authentication']:
        new_server['testing'] = True
    else:
        try:
            token = obj['authentication']['token']
            issuer = obj['authentication']['issuer']

            authx.auth.add_provider_to_tyk_api(TYK_FEDERATION_API_ID, token, issuer)
        except Exception as e:
            raise Exception(f"Failed to register server with tyk: {type(e)} {str(e)}")
        try:
            authx.auth.add_provider_to_opa(token, issuer)
        except Exception as e:
            raise Exception(f"Failed to register server with opa: {type(e)} {str(e)}")

    stored_servers_dict, status_code = authx.auth.set_service_store_secret("federation", key="servers", value=json.dumps({"servers": servers}))
    if status_code != 200:
        logger.error(f"Error in register_server: {stored_servers_dict}")
    return obj['server']


def unregister_server(server_id):
    servers = get_registered_servers()
    result = None
    if servers is not None and server_id in servers:
        result = servers.pop(server_id)
    stored_servers_dict, status_code = authx.auth.set_service_store_secret("federation", key="servers", value=json.dumps({"servers": servers}))
    if status_code != 200:
        logger.error(f"Error in register_server: {stored_servers_dict}")
    return result


def get_registered_services():
    stored_services_dict, status_code = authx.auth.get_service_store_secret("federation", key="services")
    if status_code == 404:
        # no value was found, so this must need to be initialized
        stored_services_dict, status_code = authx.auth.set_service_store_secret("federation", key="services", value=json.dumps({"services": {}}))
        return {}
    if status_code != 200:
        logger.error(f"Error in get_registered_services: {stored_services_dict}")
        return None
    return stored_services_dict["services"]


def register_service(obj):
    services = get_registered_services()
    if services is not None:
        services[obj['id']] = obj
        stored_services_dict, status_code = authx.auth.set_service_store_secret("federation", key="services", value=json.dumps({"services": services}))
        if status_code != 200:
            logger.error(f"Error in register_service: {stored_services_dict}")
            return None
    return obj


def unregister_service(service_id):
    services = get_registered_services()
    result = None
    if services is not None and service_id in services:
        result = services.pop(service_id)
        stored_services_dict, status_code = authx.auth.set_service_store_secret("federation", key="services",   value=json.dumps({"services": services}))
    return result
