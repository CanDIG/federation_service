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

    return generic_search('GET', endpoint_path, endpoint_payload)


@apilog
def post_search():
    """Wrapper for POST requests"""
    data = json.loads(flask.request.data)
    return generic_search('POST', data["endpoint_path"], data["endpoint_payload"])


def generic_search(request_type, path, payload=None):
    """

    Federate queries by forwarding request to other nodes
    and aggregating the results

    Parameters:
    ===========
    requestType: GET or POST
    path: Path to microservice endpoint - Assumed to be on the same domain
    payload: Parameters to be passed on to the endpoint

    Returns:
    ========
    response_object: json string
        Merged responses from the federation nodes. response_object structure:

    ** This still needs to be finalized **

    {
    "status": [Status Codes],
    "results": [Responses]
    }

    """
    args = {"endpoint_path": path, "endpoint_payload": payload}
    request_dictionary = flask.request
    service = path.split("/")[0]

    federation_response = FederationResponse(request_type, args, APP.config["services"][service],
                                             'application/json', request_dictionary)

    federation_response.query_service()

    # This logic is dumb

    if 'Federation' not in request_dictionary.headers or \
            request_dictionary.headers.get('Federation') == 'true':

        federation_response.handle_peer_request()




    response_object = federation_response.get_response_object()

    return response_object
