"""
Methods to handle services and peer servers
"""

import json
import authx.auth
import os
from candigv2_logging.logging import CanDIGLogger


logger = CanDIGLogger(__file__)


TYK_FEDERATION_API_ID = os.getenv("TYK_FEDERATION_API_ID")
TYK_HTSGET_API_ID = os.getenv("TYK_HTSGET_API_ID")
TYK_INGEST_API_ID = os.getenv("TYK_INGEST_API_ID")
CANDIG_USER_KEY = os.getenv("CANDIG_USER_KEY")
APPROLE_TOKEN = None
if os.getenv("TESTING", False):
    APPROLE_TOKEN = "test"

def get_registered_servers():
    stored_servers_dict, status_code = authx.auth.get_service_store_secret("federation", key="servers", token=APPROLE_TOKEN)
    if status_code == 404:
        # no value was found, so this must need to be initialized
        stored_servers_dict, status_code = authx.auth.set_service_store_secret("federation", key="servers", value=json.dumps({"servers": {}}), token=APPROLE_TOKEN)
        return {}
    if status_code != 200:
        logger.error(f"Error in get_registered_servers: {stored_servers_dict}")
        return None
    return stored_servers_dict["servers"]


def register_server(obj):
    new_server = obj['server']
    token = obj['authentication']['token']
    issuer = obj['authentication']['issuer']

    if new_server['url'].endswith("/federation"):
       new_server['url'].replace("/federation", "")

    if 'testing' in obj['authentication']:
        new_server['testing'] = True
    else:
        try:
            jwt_data = authx.auth.decode_token(token, issuer)
            client_id = jwt_data["azp"]

            # add provider to tyk: the method will check for and will not add duplicates.
            authx.auth.add_provider_to_tyk_api(TYK_FEDERATION_API_ID, token, issuer)
            authx.auth.add_provider_to_tyk_api(TYK_HTSGET_API_ID, token, issuer)

            # check to see if this exact server is already here: if so, don't add it to our servers list
            servers = get_registered_servers()
            if servers is not None:
                for s in servers.values():
                    s_client_id = authx.auth.decode_token(s["authentication"]["token"], s["authentication"]["issuer"])["azp"]
                    if s_client_id == client_id and s["authentication"]["issuer"] == issuer:
                        if s["server"]["url"] != new_server["url"]:
                            raise Exception(f"Cannot register another server with the same issuer and client")
                        return None
        except Exception as e:
            raise Exception(f"Failed to register server with tyk: {type(e)} {str(e)}")
        try:
            authx.auth.add_provider_to_opa(token, issuer)
        except Exception as e:
            raise Exception(f"Failed to register server with opa: {type(e)} {str(e)}")

    servers[new_server['id']] = obj
    stored_servers_dict, status_code = authx.auth.set_service_store_secret("federation", key="servers", value=json.dumps({"servers": servers}))
    if status_code != 200:
        logger.error(f"Error in register_server: {stored_servers_dict}")
    return obj['server']


def unregister_server(server_id):
    servers = get_registered_servers()
    result = None
    if servers is not None and server_id in servers:
        issuer = servers[server_id]["authentication"]["issuer"]
        authx.auth.remove_provider_from_tyk_api(TYK_FEDERATION_API_ID, issuer)
        authx.auth.remove_provider_from_tyk_api(TYK_HTSGET_API_ID, issuer)
        result = servers.pop(server_id)
    stored_servers_dict, status_code = authx.auth.set_service_store_secret("federation", key="servers", value=json.dumps({"servers": servers}))
    if status_code != 200:
        logger.error(f"Error in register_server: {stored_servers_dict}")
    return result


def get_registered_external_services():
    stored_external_services_dict, status_code = authx.auth.get_service_store_secret("federation", key="external_services", token=APPROLE_TOKEN)
    if status_code == 404:
        # no value was found, so this must need to be initialized
        stored_external_services_dict, status_code = authx.auth.set_service_store_secret("federation", key="external_services", value=json.dumps({"external_services": {}}), token=APPROLE_TOKEN)
        return {}
    if status_code != 200:
        logger.error(f"Error in get_registered_external_services: {stored_external_services_dict}")
        return None
    return stored_external_services_dict["external_services"]


def register_external_service(obj):
    token = obj['authentication']['token']
    issuer = obj['authentication']['issuer']

    new_external_service = {
        "service": obj["service"],
        "issuer": issuer,
        "token": token
    }

    try:
        jwt_data = authx.auth.decode_token(token, issuer)
        new_external_service["client_id"] = jwt_data["azp"]
        new_external_service["user"] = jwt_data[CANDIG_USER_KEY]

        # add provider to tyk: the method will check for and will not add duplicates.
        authx.auth.add_provider_to_tyk_api(TYK_FEDERATION_API_ID, token, issuer)
        authx.auth.add_provider_to_tyk_api(TYK_INGEST_API_ID, token, issuer)

        external_services = get_registered_external_services()
    except Exception as e:
        raise Exception(f"Failed to register external_service with tyk: {type(e)} {str(e)}")
    try:
        authx.auth.add_provider_to_opa(token, issuer)
    except Exception as e:
        raise Exception(f"Failed to register external_service with opa: {type(e)} {str(e)}")

    external_services[new_external_service["service"]] = new_external_service
    stored_external_services_dict, status_code = authx.auth.set_service_store_secret("federation", key="external_services", value=json.dumps({"external_services": external_services}))
    if status_code != 200:
        logger.error(f"Error in register_external_service: {stored_external_services_dict}")
    return new_external_service


def unregister_external_service(external_service_id):
    external_services = get_registered_external_services()
    result = None
    if external_services is not None and external_service_id in external_services:
        issuer = external_services[external_service_id]["issuer"]
        # TODO: figure out how to remove this from the API if it's the only occurrence in both external_services AND federated servers
        # authx.auth.remove_provider_from_tyk_api(TYK_FEDERATION_API_ID, issuer)
        result = external_services.pop(external_service_id)
    stored_external_services_dict, status_code = authx.auth.set_service_store_secret("federation", key="external_services", value=json.dumps({"external_services": external_services}))
    if status_code != 200:
        logger.error(f"Error in register_external_service: {stored_external_services_dict}")
    return result


def get_registered_services():
    stored_services_dict, status_code = authx.auth.get_service_store_secret("federation", key="services", token=APPROLE_TOKEN)
    if status_code == 404:
        # no value was found, so this must need to be initialized
        stored_services_dict, status_code = authx.auth.set_service_store_secret("federation", key="services", value=json.dumps({"services": {}}), token=APPROLE_TOKEN)
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
