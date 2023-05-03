"""
Methods to handle incoming requests passed from Tyk
"""

from candig_federation.api.authz import is_site_admin
import connexion
from flask import request, Flask
from candig_federation.api.logging import apilog
from candig_federation.api.federation import FederationResponse
from candig_federation.api.network import get_registered_servers, get_registered_services, register_server, register_service, unregister_server, unregister_service


app = Flask(__name__)


@apilog
def service_info():
    """
    :return: Our own server.
    """
    return list(get_registered_servers().values())[0], 200


@apilog
def list_servers():
    """
    :return: Dictionary of registered peer servers.
    """
    return list(get_registered_servers().values()), 200


@apilog
def add_server():
    """
    :return: Server added.
    """
    if not is_site_admin(request):
        return {"message": "User is not authorized to POST"}, 403
    new_server = connexion.request.json
    try:
        register_server(new_server)
        return get_registered_servers()[new_server['server']['id']], 200
    except Exception as e:
        return {"message": f"Couldn't add server: {type(e)} {str(e)}"}, 500


@apilog
@app.route('/servers/<path:id_>')
def get_server(id_):
    """
    :return: Server requested.
    """
    return get_registered_servers()[id_], 200


@apilog
@app.route('/servers/<path:id_>')
def delete_server(id_):
    """
    :return: Server deleted.
    """
    if not is_site_admin(request):
        return {"message": "User is not authorized to POST"}, 403
    result = unregister_server(id_)
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
    return get_registered_services()[id_], 200


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
        request_type = data["request_type"]
        endpoint_path = data["endpoint_path"]
        if endpoint_path[0] == "/":
            return {
                    "response": (f"Invalid endpoint_path: {endpoint_path}. "
                    "Please remove the / at the beginning: "),
                    "status": 400,
                    "service": "ErrorHandling"
                    }, 400

        endpoint_payload = data["endpoint_payload"]
        endpoint_service = data["endpoint_service"]
        microservice_URL = get_registered_services()[endpoint_service]['url']
        federation_response = FederationResponse(url=microservice_URL,
                                                request=request_type,
                                                endpoint_path=endpoint_path,
                                                endpoint_payload=endpoint_payload,
                                                request_dict=request,
                                                endpoint_service=endpoint_service
                                                )

        return federation_response.get_response_object()

    except KeyError:
        """
        Due to Connexion parsing the args prior this code running, it will be assumed that we
        have a valid request_type, endpoint_path and endpoint_payload. A KeyError occuring here
        will be due to the service dictionary receiving an invalid key.
        """
    return {
           "response": ("Invalid service name: {}. "
           "Please make sure that the service requested matches a registered service: "
           "{} "
           .format(endpoint_service, list(get_registered_services().keys()))),
           "status": 404,
           "service": "ErrorHandling"
           }, 404
