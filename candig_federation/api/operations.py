import json
import datetime

import flask

from candig_federation.api.logging import apilog, logger
from candig_federation.api.logging import structured_log as struct_log
from candig_federation.api.models import Error, BASEPATH
from candig_federation.api.federation import FederationResponse

app = flask.current_app



@apilog
def get_search(endpoint_path, endpoint_payload=None):
    print("\n -----Generic Start 4 GET-----")

    return generic_search('GET', endpoint_path, endpoint_payload)

@apilog
def post_search():

    data = json.loads(flask.request.data)

    print("\n -----Generic Start 4 POST-----")

    return generic_search('POST', data["path"], data["payload"])

@apilog
def announce():
    return "ANNOUNCE"

@apilog
def heartbeat():
    return "HEARTBEAT"


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
    responseObject: json string
        Merged responses from the federation nodes. responseObject structure:

    {
    "status": {
        "Successful communications": <number>,
        "Known peers": <number>,
        "Valid response": <true|false>,
        "Queried peers": <number>
        },
    "results": {
            "total": N
            "datasets": [
                    {record1},
                    {record2},
                    ...
                    {recordN},
                ]
            }
        ]
    }

    """
    args = {"endpoint_path": path, "endpoint_payload": payload}

    request_dictionary = flask.request

    # TODO Find correct service

    federationResponse = FederationResponse(request_type, args, app.config["services"][0], "Blank",
                                            'application/json', request_dictionary)

    federationResponse.handleLocalRequest()

    if 'federation' not in request_dictionary.headers or request_dictionary.headers.get('federation') == 'True':

        """Need to federate query"""

        federationResponse.handlePeerRequest()

    responseObject = federationResponse.getResponseObject()

    # TODO Figure out returning to Tyk

    return responseObject
