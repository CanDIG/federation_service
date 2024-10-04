"""
Methods to handle incoming requests passed from Tyk
"""

from authz import is_site_admin
import connexion
from werkzeug.exceptions import UnsupportedMediaType
from flask import request, Flask
from federation import FederationResponse
from network import get_registered_servers, get_registered_services, register_server, register_service, unregister_server, unregister_service
from candigv2_logging.logging import CanDIGLogger


logger = CanDIGLogger(__file__)


app = Flask(__name__)


def service_info():
    """
    :return: Our own server.
    """
    response = {
        "description": "Microservice implementation of CanDIGv2 federation",
        "id": "org.candig.federation",
        "name": "CanDIGv2 Federation",
        "organization": {
            "name": "CanDIG",
            "url": "https://www.distributedgenomics.ca"
        }
    }
    servers = get_registered_servers()
    if servers is not None and len(servers.values()) > 0:
        response["server"] = list(servers.values()).pop(0)
    return response, 200


def list_servers():
    """
    :return: Dictionary of registered peer servers.
    """
    servers = get_registered_servers()
    if servers is not None:
        result = map(lambda x: x["server"], servers.values())
        return list(result), 200
    logger.debug(f"Couldn't list servers", request)
    return {"message": "Couldn't list servers"}, 500


def add_server(register=False):
    """
    :return: Server added.
    """
    if not is_site_admin(request):
        return {"message": "User is not authorized to POST"}, 403
    try:
        # if register=True, list known servers in Vault and register them all
        if register:
            existing_servers = get_registered_servers()
            for server in existing_servers:
                register_server(existing_servers[server])
    except Exception as e:
        logger.debug(f"Couldn't register server", request)
        return {"message": f"Couldn't register servers: {type(e)} {str(e)} {connexion.request}"}, 500
    try:
        if connexion.request.json is not None and 'server' in connexion.request.json:
            new_server = connexion.request.json
            if register_server(new_server) is None:
                return {"message": f"Server {new_server['server']['id']} already present"}, 204
            return get_registered_servers()[new_server['server']['id']]['server'], 201
    except UnsupportedMediaType as e:
        # this is the exception that gets thrown if the requestbody is null
        return get_registered_servers(), 200
    except Exception as e:
        logger.debug(f"Couldn't register server", request)
        return {"message": f"Couldn't add server: {type(e)} {str(e)} {connexion.request}"}, 500


@app.route('/servers/<path:server_id>')
def get_server(server_id):
    """
    :return: Server requested.
    """
    servers = get_registered_servers()
    if servers is not None and server_id in servers:
        return servers[server_id], 200
    else:
        logger.debug(f"Couldn't find server {server_id}", request)
        return {"message": f"Couldn't find server {server_id}"}, 404


@app.route('/servers/<path:server_id>')
def delete_server(server_id):
    """
    :return: Server deleted.
    """
    if not is_site_admin(request):
        return {"message": "User is not authorized to POST"}, 403
    result = unregister_server(server_id)
    if result is None:
        logger.debug(f"Server not found", request)
        return {"message": f"Server {server_id} not found"}, 404
    return result, 200


def list_services():
    """
    :return: Dictionary of registered services.
    """
    return list(get_registered_services().values()), 200


@app.route('/services/<path:service_id>')
def get_service(service_id):
    """
    :return: Service requested.
    """
    services = get_registered_services()
    if services is not None and service_id in services:
        return services[service_id], 200
    else:
        logger.debug(f"Couldn't find service {service_id}", request)
        return {"message": f"Couldn't find service {service_id}"}, 404


def add_service(register=False):
    """
    :return: Service added.
    """
    if not is_site_admin(request):
        return {"message": "User is not authorized to POST"}, 403
    try:
        # if register=True, list known services in Vault and register them all
        if register:
            existing_services = get_registered_services()
            for service in existing_services:
                register_service(existing_services[service])
        new_service = connexion.request.json
        register_service(new_service)
    except UnsupportedMediaType as e:
        # this is the exception that gets thrown if the requestbody is null
        return get_registered_services(), 200
    except Exception as e:
        logger.debug(f"Couldn't add service", request)
        return {"message": f"Couldn't add service: {type(e)} {str(e)} {connexion.request}"}, 500
    return get_registered_services()[new_service['id']], 200


@app.route('/services/<path:service_id>')
def delete_service(service_id):
    """
    :return: Service deleted.
    """
    if not is_site_admin(request):
        return {"message": "User is not authorized to POST"}, 403
    result = unregister_service(service_id)
    if result is None:
        logger.debug(f"Couldn't find service", request)
        return {"message": f"Service {service_id} not found"}, 404
    return result, 200


def post_search():
    """
    Send a POST request to CanDIG services and possibly federate it.
    Method defined by federation.yaml OpenAPI document.
    Retrieves an endpoint_path and endpoint_payload from POST request body,
    following the endpoint_path conventions set in get_search().
    The endpoint_payload is microservice specific but will typically be a
    JSON object of sorts.

    :return: response_object
    response_object: json string
    Merged responses from the federation nodes. response_object structure:
    ** This still needs to be finalized **
    {
    "status": Status,
    "results": [Response],
    "service": ServiceName
    }

    Status - Aggregate HTTP response code
    Response - List of service specific responses
    ServiceName - Name of service (used for logstash tagging)
    """
    try:
        logger.debug("Sending federated request", request)
        data = connexion.request.json
        request_type = data["method"]
        endpoint_path = data["path"]
        if endpoint_path[0] == "/":
            return {
                    "response": (f"Invalid endpoint path: {endpoint_path}. "
                    "Please remove the / at the beginning: "),
                    "status": 400,
                    "service": "ErrorHandling"
                    }, 400

        endpoint_payload = data["payload"]
        endpoint_service = data["service"]
        federation_response = FederationResponse(
            request=request_type,
            endpoint_path=endpoint_path,
            endpoint_payload=endpoint_payload,
            request_dict=request,
            endpoint_service=endpoint_service,
            unsafe="unsafe" in data
        )

        return federation_response.get_response_object()

    except Exception as e:
        """
        Due to Connexion parsing the args prior this code running, it will be assumed that we
        have a valid request_type, endpoint_path and endpoint_payload. A KeyError occuring here
        will be due to the service dictionary receiving an invalid key.
        """
        logger.error(f"{type(e)} {str(e)}", request)
        return {
               "response": f"{type(e)} {str(e)}",
               "status": 404,
               "service": "ErrorHandling"
               }, 404
