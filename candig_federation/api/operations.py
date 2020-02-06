"""
Methods to handle incoming requests passed from Tyk

"""

import json
import flask
from candig_federation.api.logging import apilog
from candig_federation.api.federation import FederationResponse

APP = flask.current_app


@apilog
def get_search(endpoint_path, endpoint_payload=None):
    """
    Parameters:
    ===========

    path: Path to microservice endpoint - Assumed to be on the same domain
    payload: Parameters to be passed on to the endpoint

    Returns:
    ========
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
    service = endpoint_path.split("/")[0]
    microservice = APP.config['services'][service]
    federation_response = FederationResponse(url=microservice,
                                             request='GET',
                                             endpoint_path=endpoint_path,
                                             endpoint_payload=endpoint_payload,
                                             request_dict=flask.request,
                                             service=service)

    return federation_response.get_response_object()



@apilog
def post_search():
    """
    Parameters:
    ===========

    path: Path to microservice endpoint - Assumed to be on the same domain
    payload: Parameters to be passed on to the endpoint

    Returns:
    ========
    response_object: json string
        Merged responses from the federation nodes. response_object structure:

    ** This still needs to be finalized **

    {
    "status": [Status Codes],
    "results": Responses
    }

    """
    data = json.loads(flask.request.data)
    endpoint_path = data["endpoint_path"]
    endpoint_payload = data["endpoint_payload"]
    service = endpoint_path.split("/")[0]
    microservice = APP.config['services'][service]
    federation_response = FederationResponse(url=microservice,
                                             request='POST',
                                             endpoint_path=endpoint_path,
                                             endpoint_payload=endpoint_payload,
                                             request_dict=flask.request,
                                             service=service)
    return federation_response.get_response_object()

