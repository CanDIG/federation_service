from unittest.mock import Mock, patch

from werkzeug.datastructures import Headers
import sys
import os
import json
from functools import reduce

import pytest
from requests import exceptions

sys.path.append("{}/{}".format(os.getcwd(), "candig_federation"))

sys.path.append(os.getcwd())

from candig_federation.__main__ import APP
from candig_federation.api.federation import FederationResponse
from candig_federation.api import operations
from tests.test_data.test_structs import *

APP.app.config["peers"] = {"p1": "http://10.9.208.132:6000", "p2": "http://10.9.208.132:8000"}
APP.app.config["services"] = {
    "rnaget": 'http://{}:{}'.format(TP["URI"], TP["PORT0"]),
    "datasets": "http://10.9.208.132:19712",
    "datasetsP": "https://ff345ede-96fd-4357-bc44-80ba503591b3.mock.pstmn.io"
}
APP.app.config["local"] = "http://10.9.208.132:6000"


@pytest.fixture()
def client():
    context = APP.app.app_context()

    return context


# Taken from https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
def mocked_service_get(*args, **kwargs):
    if args[0] == 'http://{}:{}/rnaget/projects'.format(TP["URI"], TP["PORT0"]):
        return AP["s1"]
    elif args[0] == 'http://{}:{}/rnaget/projects'.format(TP["URI"], TP["PORT1"]):
        return AP["s2"]

    return AP["fail"]


def mocked_service_post(*args, **kwargs):
    if args[0] == 'http://{}:{}/rnaget/projects'.format(TP["URI"], TP["PORT0"]):
        return PR["PLV1"]
    elif args[0] == 'http://{}:{}/variants/all'.format(TP["URI"], TP["PORT0"]):
        return PR["PLV2"]

    return AP["fail"]


# The returns from async requests need to be futures, so a second class is used to represent that

def mocked_async_requests_get(*args, **kwargs):
    if args[0] == 'http://{}'.format(TP["Tyk1"]):
        return AP["i1"]
    elif args[0] == 'http://{}'.format(TP["Tyk2"]):
        return AP["i2"]

    return AP["fail"]


def mocked_async_requests_post(*args, **kwargs):
    if args[0] == 'http://{}'.format(TP["Tyk1"]):
        return PR["iPLV1"]
    elif args[0] == 'http://{}'.format(TP["Tyk2"]):
        return PR["iPLV2"]

    return AP["fail"]



###################
# Testing Portion #
###################


@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_service_get)
def test_valid_noFed_get(mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="GET",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        RO = FR.get_response_object()
        assert RO["status"] == 200
        assert RO["results"] == [AP["v1"]]


@patch('candig_federation.api.federation.requests.Session.post', side_effect=mocked_service_post)
def test_valid_noFed_post(mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="POST",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        RO = FR.get_response_object()
        assert RO["status"] == 200
        assert RO["results"] == [PostListV1]


@patch('candig_federation.api.federation.requests.Session.get', side_effect=exceptions.ConnectionError)
def test_invalid_noFed_get(mock_requests, client):
    with client:
        url = "http:2132{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="GET",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        RO = FR.get_response_object()
        assert RO["status"] == 404
        assert RO["results"] == []


@patch('candig_federation.api.federation.requests.Session.post', side_effect=exceptions.ConnectionError)
def test_invalid_noFed_post(mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="POST",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        RO = FR.get_response_object()
        assert RO["status"] == 404
        assert RO["results"] == []


@patch('candig_federation.api.federation.requests.Session.get', side_effect=exceptions.Timeout)
def test_timeout_noFed_get(mock_requests, client):
    with client:
        url = "http:{}:{}".format('0.0.0.0', TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="GET",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        RO = FR.get_response_object()
        assert RO["status"] == 408
        assert RO["results"] == []


@patch('candig_federation.api.federation.requests.Session.post', side_effect=exceptions.Timeout)
def test_timeout_noFed_post(mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="POST",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        RO = FR.get_response_object()
        assert RO["status"] == 408
        assert RO["results"] == []


@patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_async_requests_get)
def test_valid_asyncRequests_two_peers_get(mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="GET",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        resp = FR.async_requests(uri_list=["http://{}".format(TP["Tyk1"]),
                                           "http://{}".format(TP["Tyk2"])],
                                 request_type='GET',
                                 endpoint_path=TP["path"],
                                 endpoint_payload="",
                                 header=TP["Headers"])

        Success = list(filter(lambda x: x == 200, map(lambda a: a.status_code, resp)))

        assert len(resp) == 2
        assert Success == [200, 200]


@patch('candig_federation.api.federation.FuturesSession.post', side_effect=mocked_async_requests_post)
def test_valid_asyncRequests_two_peers_post(mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="POST",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        resp = FR.async_requests(uri_list=["http://{}".format(TP["Tyk1"]),
                                           "http://{}".format(TP["Tyk2"])],
                                 request_type='POST',
                                 endpoint_path=TP["path"],
                                 endpoint_payload="",
                                 header=TP["Headers"])

        Success = list(filter(lambda x: x == 200, map(lambda a: a.status_code, resp)))

        assert len(resp) == 2
        assert Success == [200, 200]


@patch('candig_federation.api.federation.FuturesSession.get', side_effect=exceptions.ConnectionError)
def test_invalid_asyncRequests_two_peers_get(mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="GET",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        resp = FR.async_requests(uri_list=["http://{}".format(TP["Tyk1"]),
                                           "http://{}".format(TP["Tyk2"])],
                                 request_type='GET',
                                 endpoint_path=TP["path"],
                                 endpoint_payload="",
                                 header=TP["Headers"])

        ConnErrs = list(map(lambda a: isinstance(a, exceptions.ConnectionError), resp))

        # Error should just be propagated through since handle_peer_request will address it

        assert len(resp) == 2
        assert ConnErrs == [True, True]


@patch('candig_federation.api.federation.FuturesSession.post', side_effect=exceptions.ConnectionError)
def test_invalid_asyncRequests_two_peers_post(mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="POST",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        resp = FR.async_requests(uri_list=["http://{}".format(TP["Tyk1"]),
                                           "http://{}".format(TP["Tyk2"])],
                                 request_type='POST',
                                 endpoint_path=TP["path"],
                                 endpoint_payload="",
                                 header=TP["Headers"])

        Success = list(map(lambda a: isinstance(a, exceptions.ConnectionError), resp))

        assert len(resp) == 2
        assert Success == [True, True]


@patch('candig_federation.api.federation.FuturesSession.post', side_effect=exceptions.Timeout)
def test_timeout_asyncRequests_two_peers_post(mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="POST",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        resp = FR.async_requests(uri_list=["http://{}".format(TP["Tyk1"]),
                                           "http://{}".format(TP["Tyk2"])],
                                 request_type='POST',
                                 endpoint_path=TP["path"],
                                 endpoint_payload="",
                                 header=TP["Headers"])

        Success = list(map(lambda a: isinstance(a, exceptions.Timeout), resp))

        assert len(resp) == 2
        assert Success == [True, True]


@patch('candig_federation.api.federation.FuturesSession.get', side_effect=exceptions.Timeout)
def test_timeout_asyncRequests_two_peers_get(mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="GET",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Headers"])

        resp = FR.async_requests(uri_list=["http://{}".format(TP["Tyk1"]),
                                           "http://{}".format(TP["Tyk2"])],
                                 request_type='GET',
                                 endpoint_path=TP["path"],
                                 endpoint_payload="",
                                 header=TP["Headers"])

        TimeoutErrs = list(map(lambda a: isinstance(a, exceptions.Timeout), resp))

        # Error should just be propagated through since handle_peer_request will address it

        assert len(resp) == 2
        assert TimeoutErrs == [True, True]


"""
This test focuses on the output from FederationResponse.handle_peer_request(). To efficiently test it, the response
from from async_requests will be mocked to resemble the expected output from FederationResponse.handleLocalRequest().
"""


@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_service_get)
@patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_async_requests_get)
def test_valid_PeerRequest_one_peer_get(mock_requests, mock_session, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="GET",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Federate"])

        RO = FR.get_response_object()

        assert RO["status"] == 200
        assert RO["results"] == [AP["v1"], AP["v2"]]


"""
This test will focus on the operations.get_search() function. A valid GET query will be sent to be federated. Both
FederationResponse.handleLocalRequest() and FederationResponse.handle_peer_request() will be rerouted to mocked services
to retrieve data
"""


@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_service_get)
@patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_async_requests_get)
def test_valid_federated_query_one_peer_get(mock_requests, mock_session, client):
    with client:
        with APP.app.test_request_context(
                data={}, headers=Headers(fedHeader.headers)
        ):
            RO = operations.get_search(TP["path"], "")

            assert RO["status"] == 200
            assert RO["results"] == [AP["v1"], AP["v2"]]


@patch('candig_federation.api.federation.requests.Session.post', side_effect=mocked_service_post)
@patch('candig_federation.api.federation.FuturesSession.post', side_effect=mocked_async_requests_post)
def test_valid_PeerRequest_one_peer_post(mock_session, mock_requests, client):
    with client:
        url = "http://{}:{}".format(TP['URI'], TP['PORT0'])
        FR = FederationResponse(url=url,
                                request="POST",
                                endpoint_payload="",
                                endpoint_path=TP["path"],
                                request_dict=TP["Federate"])

        RO = FR.get_response_object()

        assert RO["status"] == 200
        assert RO["results"] == [PostListV1, PostListV2]


@patch('candig_federation.api.federation.requests.Session.post', side_effect=mocked_service_post)
@patch('candig_federation.api.federation.FuturesSession.post', side_effect=mocked_async_requests_post)
def test_valid_federated_query_one_peer_post(mock_requests, mock_session, client):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"endpoint_path": TP["path"],
                                 "endpoint_payload": ""}),
                headers=Headers(fedHeader.headers)
        ):
            RO = operations.post_search()

            assert RO["status"] == 200
            assert RO["results"] == [PostListV1, PostListV2]

# Test Federation with one peer, have local error out -------------------------------------------------

@patch('candig_federation.api.federation.requests.Session.post', side_effect=exceptions.ConnectionError)
@patch('candig_federation.api.federation.FuturesSession.post', side_effect=mocked_async_requests_post)
def test_valid_federated_local_ConnErr_one_peer_post(mock_session,  client):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"endpoint_path": TP["path"],
                                 "endpoint_payload": ""}),
                headers=Headers(fedHeader.headers)
        ):
            RO = operations.post_search()
            assert RO["status"] == 200
            assert RO["results"] == [PostListV2]


@patch('candig_federation.api.federation.requests.Session.post', side_effect=exceptions.Timeout)
@patch('candig_federation.api.federation.FuturesSession.post', side_effect=mocked_async_requests_post)
def test_valid_federated_local_TimeOut_one_peer_post(mock_session,  client):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"endpoint_path": TP["path"],
                                 "endpoint_payload": ""}),
                headers=Headers(fedHeader.headers)
        ):
            RO = operations.post_search()
            assert RO["status"] == 200
            assert RO["results"] == [PostListV2]


@patch('candig_federation.api.federation.requests.Session.get', side_effect=exceptions.ConnectionError)
@patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_async_requests_get)
def test_valid_federated_local_ConnErr_one_peer_get(mock_requests, mock_session, client):
    with client:
        with APP.app.test_request_context(
                data={}, headers=Headers(fedHeader.headers)
        ):
            RO = operations.get_search(TP["path"], "")
            assert RO["status"] == 200
            assert RO["results"] == [AP["v2"]]


@patch('candig_federation.api.federation.requests.Session.get', side_effect=exceptions.Timeout)
@patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_async_requests_get)
def test_valid_federated_local_TimeOut_one_peer_get(mock_requests, mock_session, client):
    with client:
        with APP.app.test_request_context(
                data={}, headers=Headers(fedHeader.headers)
        ):
            RO = operations.get_search(TP["path"], "")
            assert RO["status"] == 200
            assert RO["results"] == [AP["v2"]]


# Test Federation with one peer, have peer error out --------------------------------------------------

@patch('candig_federation.api.federation.requests.Session.post', side_effect=mocked_service_post)
@patch('candig_federation.api.federation.FuturesSession.post', side_effect=exceptions.ConnectionError)
def test_ConnErr_federated_valid_local_one_peer_post(mock_session,  client):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"endpoint_path": TP["path"],
                                 "endpoint_payload": ""}),
                headers=Headers(fedHeader.headers)
        ):
            RO = operations.post_search()
            assert RO["status"] == 200
            assert RO["results"] == [PostListV1]


@patch('candig_federation.api.federation.requests.Session.post', side_effect=mocked_service_post)
@patch('candig_federation.api.federation.FuturesSession.post', side_effect=exceptions.Timeout)
def test_TimeOut_federated_valid_local_one_peer_post(mock_session,  client):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"endpoint_path": TP["path"],
                                 "endpoint_payload": ""}),
                headers=Headers(fedHeader.headers)
        ):
            RO = operations.post_search()
            assert RO["status"] == 200
            assert RO["results"] == [PostListV1]


@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_service_get)
@patch('candig_federation.api.federation.FuturesSession.get', side_effect=exceptions.ConnectionError)
def test_ConnErr_federated_valid_local_one_peer_get(mock_requests, mock_session, client):
    with client:
        with APP.app.test_request_context(
                data={}, headers=Headers(fedHeader.headers)
        ):
            RO = operations.get_search(TP["path"], "")
            assert RO["status"] == 200
            assert RO["results"] == [AP["v1"]]


@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_service_get)
@patch('candig_federation.api.federation.FuturesSession.get', side_effect=exceptions.Timeout)
def test_TimeOut_federated_valid_local_one_peer_get(mock_requests, mock_session, client):
    with client:
        with APP.app.test_request_context(
                data={}, headers=Headers(fedHeader.headers)
        ):
            RO = operations.get_search(TP["path"], "")
            assert RO["status"] == 200
            assert RO["results"] == [AP["v1"]]
