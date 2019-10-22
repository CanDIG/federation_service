"""
Methods to handle incoming requests passed from Tyk

"""

import json
import flask

from distutils.util import strtobool

from candig_federation.api.logging import apilog
from candig_federation.api.federation import FederationResponse

APP = flask.current_app



@apilog
def get_search(endpoint_path, endpoint_payload=None):
    """Wrapper for GET requests"""

    service = endpoint_path.split("/")[0]
    microservice = APP.config['services'][service]
    federation_response = FederationResponse(url=microservice,
                                             request='GET',
                                             endpoint_path=endpoint_path,
                                             endpoint_payload=endpoint_payload,
                                             request_dict=flask.request)
    response = federation_response.get_response_object()

    return response


@apilog
def post_search():
    """Wrapper for POST requests"""
    data = json.loads(flask.request.data)
    endpoint_path = data["endpoint_path"]
    endpoint_payload = data["endpoint_payload"]
    service = endpoint_path.split("/")[0]
    microservice = APP.config['services'][service]
    federation_response = FederationResponse(url=microservice,
                                             request='POST',
                                             endpoint_path=endpoint_path,
                                             endpoint_payload=endpoint_payload,
                                             request_dict=flask.request)
    response = federation_response.get_response_object()
    return response


# def generic_search(request_type, path, payload=None):
#     """
#
#     Federate queries by forwarding request to other nodes
#     and aggregating the results
#
#     Parameters:
#     ===========
#     requestType: GET or POST
#     path: Path to microservice endpoint - Assumed to be on the same domain
#     payload: Parameters to be passed on to the endpoint
#
#     Returns:
#     ========
#     response_object: json string
#         Merged responses from the federation nodes. response_object structure:
#
#     ** This still needs to be finalized **
#
#     {
#     "status": [Status Codes],
#     "results": [Responses]
#     }
#
#     """
#     args = {"endpoint_path": path, "endpoint_payload": payload}
#
#
#     federation_response = FederationResponse(request_dictionary)
#
#     federation_response.query_service()
#
#     # This logic is dumb
#
#     if 'Federation' not in request_dictionary.headers or \
#             request_dictionary.headers.get('Federation') == 'true':
#
#         federation_response.handle_peer_request()
#
#
#
#
#     response_object = federation_response.get_response_object()
#
#     return response_object
