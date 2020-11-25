"""
Methods to handle incoming requests passed from Tyk
"""


import json
import flask
import sys
from candig_federation.api.logging import apilog
from candig_federation.api.federation import FederationResponse

APP = flask.current_app

  
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

        data = json.loads(flask.request.data)
        request_type = data["request_type"]
        endpoint_path = data["endpoint_path"]
        endpoint_payload = data["endpoint_payload"]
        service = endpoint_path.split("/")[0]
        microservice = APP.config['services'][service]
        federation_response = FederationResponse(url=microservice,
                                                request=request_type,
                                                endpoint_path=endpoint_path,
                                                endpoint_payload=endpoint_payload,
                                                request_dict=flask.request,
                                                service=service)
        return federation_response.get_response_object()

    except KeyError:
        """     
        Due to Connexion parsing the args prior this code running, it will be assumed that we
        have a valid request_type, endpoint_path and endpoint_payload. A KeyError occuring here 
        will be due to the service dictionary receiving an invalid key.
        """
        return {
            "response": """
            Invalid service name: {}.
            Please make sure that the beginning of your endpoint_path matches a registered service:
            {}
            """.format(service, APP.config['services'].keys()),
            "status": 404,
            "service": "ErrorHandling"
            }
    
    except :
        """     
        Ideally nothing ever reaches this error handler
        """
    return {
            "response": sys.exc_info()[0],
            "status": 500,
            "service": "ErrorHandling"
            }
    