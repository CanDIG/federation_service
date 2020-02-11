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
    """Send a GET request to CanDIG services and possibly federate it. Method defined by federation.yaml OpenAPI document.

    :param endpoint_path: Full path of API endpoint such as ``datasets/search``
    :type endpoint_path: str
    :param endpoint_payload: Query parameters as key=value strings: ``{ "param1=value1", "param2=value2" }``
    :type endpoint_payload: object
    :return: response_object


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
