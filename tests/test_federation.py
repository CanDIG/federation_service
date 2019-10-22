from unittest.mock import Mock, patch

from werkzeug.datastructures import Headers
import sys
import os
from functools import reduce

import pytest
from requests import Response

sys.path.append("{}/{}".format(os.getcwd(), "candig_federation"))

sys.path.append(os.getcwd())


from candig_federation.__main__ import APP
from candig_federation.api import operations
from candig_federation.api.federation import FederationResponse

from tests.test_data.test_structs import *





APP.app.config["peers"] = {"p1": "http://10.9.208.132:6000", "p2": "http://10.9.208.132:8000"}
APP.app.config["self"] = "http://10.9.208.132:8890"

@pytest.fixture()
def client():
    context = APP.app.app_context()

    return context


# Taken from https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
def mocked_service_get(*args, **kwargs):
    if args[0] == 'http://{}:{}/rnaget/projects'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT0"]):
        return ANSWER_PARAMS["s1"]
    elif args[0] == 'http://{}:{}/rnaget/projects'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT1"]):
        return ANSWER_PARAMS["s2"]

    return ANSWER_PARAMS["fail"]


def mocked_requests_post(*args, **kwargs):
    if args[0] == 'http://{}:{}/rnaget/projects'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT0"]):
        return ANSWER_PARAMS["s1"]
    elif args[0] == 'http://{}:{}/variants/all'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT0"]):
        return MockResponse(POST_RESPONSES["PLV1"], 200)

    return MockResponse(None, 404)


def mocked_async_requests_get(*args, **kwargs):
    if args[0] == 'http://{}'.format(TESTING_PARAMS["Tyk1"]):
        return ANSWER_PARAMS["s1"]
    elif args[0] == 'http://{}'.format(TESTING_PARAMS["Tyk2"]):
        return ANSWER_PARAMS["s2"]

    return ANSWER_PARAMS["fail"]


def mocked_peer_requests_get(*args, **kwargs):
    if args[0] == 'http://{}'.format(TESTING_PARAMS["Tyk1"]):
        return ANSWER_PARAMS["s1"]
    elif args[0] == 'http://{}'.format(TESTING_PARAMS["Tyk2"]):
        return ANSWER_PARAMS["s2"]

    return ANSWER_PARAMS["fail"]


def mocked_peer_requests_post(*args, **kwargs):
    if args[0] == 'http://{}:{}/federation/search'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT0"]):
        return MockResponse(
            POST_RESPONSES["PLV1"], 200)
    elif args[0] == 'http://{}:{}/federation/search'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT1"]):
        return MockResponse(
            POST_RESPONSES["PLV2"], 200)

    return ANSWER_PARAMS["fail"]

###################
# Testing Portion #
###################

@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_service_get)
def test_valid_noFed_get(mock_requests, client):
    with client:

        url = "http://{}:{}".format(TESTING_PARAMS['URI'], TESTING_PARAMS['PORT0'])
        FR = FederationResponse(url=url,
                                request="GET",
                                endpoint_payload="",
                                endpoint_path="rnaget/projects",
                                request_dict=exampleHeaders)


        RO = FR.get_response_object()

        assert RO["status"] == [200]

        assert RO["results"] == [ANSWER_PARAMS["v1"]]


# @patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_service_get)
# def test_invalid_noFed_get(mock_requests, client):
#     with client:
#         args = {
#             "endpoint_path": "rnaget/projects",
#             "endpoint_payload": ""
#         }
#         FR = FederationResponse('GET', args, "http://io.com", "application/json", TESTING_PARAMS["Headers"])
#
#         FR.query_service()
#
#         RO = FR.get_response_object()
#
#         assert RO["status"] == [404]
#
#         assert RO["results"] == []


# @patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_async_requests_get)
# def test_valid_asyncRequests_two_peers_get(mock_requests, client):
#     with client:
#         args = {
#             "endpoint_path": "rnaget/projects",
#             "endpoint_payload": ""
#         }
#         FR = FederationResponse('GET', args, "{}", "application/json", TESTING_PARAMS["Headers"])
#
#         resp = FR.async_requests(["http://{}", "http://{}".
#                                  format(TESTING_PARAMS["Tyk1"], TESTING_PARAMS["Tyk2"])],
#                                  'GET', TESTING_PARAMS["Headers"])
#
#         bools = reduce(lambda a, b: a and b,
#                     map(lambda a: True if a == 200 else False,
#                         map(lambda a: a.status_code, resp)))
#
#         assert len(resp) == 2
#         assert bools
#
# """
# This test focuses on the output from FederationResponse.handle_peer_request(). To efficiently test it, the response
# from from async_requests will be mocked to resemble the expected output from FederationResponse.handleLocalRequest().
# """
#
#
# @patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_service_get)
# @patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_peer_requests_get)
# def test_valid_PeerRequest_one_peer_get(mock_requests, mock_session, client):
#     with client:
#         args = {
#             "endpoint_path": "rnaget/projects",
#             "endpoint_payload": ""
#         }
#
#
#
#         FR = FederationResponse('GET', args, "http://10.9.208.132:8890", "application/json", TESTING_PARAMS["Headers"])
#         FR.query_service()
#         FR.handle_peer_request()
#         RO = FR.get_response_object()
#
#         assert RO["results"] == [ANSWER_PARAMS["v1"], ANSWER_PARAMS["v2"]]

#
# """
# This test will focus on the operations.get_search() function. A valid GET query will be sent to be federated. Both
# FederationResponse.handleLocalRequest() and FederationResponse.handle_peer_request() will be rerouted to mocked services
# to retrieve data
# """
#
#
# @patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_service_get)
# @patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_peer_requests_get)
# def test_valid_federated_query_one_peer_get(mock_requests, mock_session, client):
#
#     headerObj = Headers()
#
#     headerObj.add('content-type', 'application/json')
#     headerObj.add('accept', 'application/json')
#     headerObj.add('federation', "True")
#
#     with client:
#         with APP.app.test_request_context(
#             data={}, headers=headerObj
#         ):
#             args = {
#                 "endpoint_path": "rnaget/projects",
#                 "endpoint_payload": ""
#             }
#             RO = operations.get_search(args["endpoint_path"], args["endpoint_payload"])
#
#             assert RO["results"] == [{
#                 "projects": {
#                     "Umbrella": "Biochemical",
#                     "Parasol": "Microbial",
#                     "Umbra": "Chemical"
#                 }},
#                 {"key2": "value2"}]
#
#
# @patch('candig_federation.api.federation.requests.Session.post', side_effect=mocked_requests_post)
# @patch('candig_federation.api.federation.FuturesSession.post', side_effect=mocked_peer_requests_post)
# def test_valid_PeerRequest_one_peer_post(mock_session, mock_requests,  client):
#     with client:
#         args = {
#             "endpoint_path": "variants/all",
#             "endpoint_payload": ""
#         }
#         FR = FederationResponse('POST', args, "http://10.9.208.132:8890", "application/json", TESTING_PARAMS["Headers"])
#         FR.query_service()
#         PR = FR.handle_peer_request()
#         RO = FR.get_response_object()
#
#         assert RO["results"] == [POST_RESPONSES["PLV1"], POST_RESPONSES["PLV2"]]
#
#
# @patch('candig_federation.api.federation.FuturesSession.post', side_effect=mocked_peer_requests_post)
# def test_valid_PeerRequest_no_local_one_peer_post(mock_session,  client):
#     with client:
#         args = {
#             "endpoint_path": "variants/all",
#             "endpoint_payload": ""
#         }
#         FR = FederationResponse('POST', args, "http://10.9.208.132:8890", "application/json", TESTING_PARAMS["Headers"])
#         FR.query_service()
#         PR = FR.handle_peer_request()
#         RO = FR.get_response_object()
#
#
#
#         assert RO["results"] == POST_RESPONSES["PLV2"]