import json
import datetime

import flask

from candig_federation.api.logging import apilog, logger
from candig_federation.api.logging import structured_log as struct_log
from candig_federation.api.models import Error, BASEPATH

app = flask.current_app


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

    if flask.request.headers.get('federation'):
        if flask.request.headers['federation'] == "False":
            """Pass onward to microservice"""

            print("PATH:{}\nPAYLOAD:{}".format(path, payload))

            return "GET SEARCH RETURN"

    else:
        """Need to federate query"""

        print(flask.request.headers['federation'])

        # send to federation node

        # send to service

        # Send results to aggregate script

        print("Need to Federate")

        return "GET FEDERATE"




def post_search():
    return "POST SEARCH RETURN"