import json
import datetime

import flask

from candig_federation.api.logging import apilog, logger
from candig_federation.api.logging import structured_log as struct_log
from candig_federation.api.models import Error, BASEPATH
from candig_federation.api.federation import FederationResponse

app = flask.current_app

url = "https://ff345ede-96fd-4357-bc44-80ba503591b3.mock.pstmn.io"

@apilog
def get_search(path, payload=None):
    """

    Federate GET queries by forwarding request to other nodes
    and aggregating the result

    Parameters:
    ===========
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

    request_dictionary = flask.request
    federationResponse = FederationResponse('GET', path, url, "Blank",
                                            'application/json', request_dictionary)

    federationResponse.handleLocalRequest()

    if 'federation' not in request_dictionary.headers or request_dictionary.headers.get('federation') == 'True':

        """Need to federate query"""



        # send to federation node

        # send to service

        # Send results to aggregate script

        federationResponse.handlePeerRequest('GET')

    print(federationResponse.getResponseObject())



def post_search():
    return "POST SEARCH RETURN"

@apilog
def announce():
    return "ANNOUNCE"

@apilog
def heartbeat():
    return "HEARTBEAT"