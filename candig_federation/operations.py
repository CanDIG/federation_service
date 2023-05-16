"""
Methods to handle incoming requests passed from Tyk
"""

from authz import is_site_admin
import connexion
from flask import request, Flask
from apilog import apilog
from federation import FederationResponse
from network import get_registered_servers, get_registered_services, register_server, register_service, unregister_server, unregister_service


app = Flask(__name__)


@apilog
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


@apilog
def list_servers():
    """
    :return: Dictionary of registered peer servers.
    """
    servers = get_registered_servers()
    if servers is not None:
        return list(servers.values()), 200
    return {"message": "Couldn't list servers"}, 500


@apilog
def add_server():
    """
    :return: Server added.
    """
    if not is_site_admin(request):
        return {"message": "User is not authorized to POST"}, 403
    try:
        new_server = connexion.request.json
        if register_server(new_server) is None:
            return {"message": f"Server {new_server['server']['id']} already present"}, 204
        return get_registered_servers()[new_server['server']['id']], 201
    except Exception as e:
        return {"message": f"Couldn't add server: {type(e)} {str(e)}"}, 500


@apilog
@app.route('/servers/<path:id_>')
def get_server(id_):
    """
    :return: Server requested.
    """
    servers = get_registered_servers()
    if servers is not None and id_ in servers:
        return servers[id_], 200
    else:
        return {"message": f"Couldn't find server {id_}"}, 404


@apilog
@app.route('/servers/<path:id_>')
def delete_server(id_):
    """
    :return: Server deleted.
    """
    if not is_site_admin(request):
        return {"message": "User is not authorized to POST"}, 403
    result = unregister_server(id_)
    if result is None:
        return {"message": f"Server {id_} not found"}, 404
    return result, 200


@apilog
def list_services():
    """
    :return: Dictionary of registered services.
    """
    return list(get_registered_services().values()), 200


@apilog
@app.route('/services/<path:id_>')
def get_service(id_):
    """
    :return: Service requested.
    """
    services = get_registered_services()
    if services is not None and id_ in services:
        return services[id_], 200
    else:
        return {"message": f"Couldn't find service {id_}"}, 404


@apilog
def add_service():
    """
    :return: Service added.
    """
    if not is_site_admin(request):
        return {"message": "User is not authorized to POST"}, 403
    new_service = connexion.request.json
    register_service(new_service)
    return get_registered_services()[new_service['id']], 200


@apilog
@app.route('/services/<path:id_>')
def delete_service(id_):
    """
    :return: Service deleted.
    """
    if not is_site_admin(request):
        return {"message": "User is not authorized to POST"}, 403
    result = unregister_service(id_)
    if result is None:
        return {"message": f"Service {id_} not found"}, 404
    return result, 200


@apilog
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
            endpoint_service=endpoint_service
        )

        return federation_response.get_response_object()

    except Exception as e:
        """
        Due to Connexion parsing the args prior this code running, it will be assumed that we
        have a valid request_type, endpoint_path and endpoint_payload. A KeyError occuring here
        will be due to the service dictionary receiving an invalid key.
        """
        return {
               "response": f"{type(e)} {str(e)}",
               "status": 404,
               "service": "ErrorHandling"
               }, 404
