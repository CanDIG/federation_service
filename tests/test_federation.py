from unittest.mock import Mock, patch

from werkzeug.datastructures import Headers
import sys
import os

import pytest

sys.path.append("{}/{}".format(os.getcwd(), "candig_federation"))

sys.path.append(os.getcwd())


from candig_federation.__main__ import APP
from candig_federation.api import operations
from candig_federation.api.federation import FederationResponse

from tests.test_data.test_structs import POST_RESPONSES

TESTING_PARAMS = {
    "URI": "10.9.208.132",
    "PORT0": "8890",
    "PORT1": "8891"
}


@pytest.fixture()
def client():
    context = APP.app.app_context()

    return context


# Taken from https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def status_code(self):
            return self.status_code

    if args[0] == 'http://{}:{}/rnaget/projects'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT0"]):
        return MockResponse({
            "projects": {
                "Umbrella": "Biochemical",
                "Parasol": "Microbial",
                "Umbra": "Chemical"
            },
            "headers": {
                "x-forwarded-proto": "https",
                "host": "postman-echo.com",
                "accept": "*/*",
                "accept-encoding": "gzip, deflate",
                "cache-control": "no-cache",
                "postman-token": "de9f0868-b9cb-4cac-96bc-fa51e8d1e32b",
                "user-agent": "PostmanRuntime/7.15.0",
                "x-forwarded-port": "443"
            },
            "url": "http://info.com/rnaget/projects"
        }, 200)
    elif args[0] == 'http://{}:{}/rnaget/projects'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT0"]):
        return MockResponse({"key2": "value2"}, 200)

    return MockResponse(None, 404)


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def status_code(self):
            return self.status_code

    if args[0] == 'http://{}:{}/rnaget/projects'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT0"]):
        return MockResponse({
            "projects": {
                "Umbrella": "Biochemical",
                "Parasol": "Microbial",
                "Umbra": "Chemical"
            },
            "headers": {
                "x-forwarded-proto": "https",
                "host": "postman-echo.com",
                "accept": "*/*",
                "accept-encoding": "gzip, deflate",
                "cache-control": "no-cache",
                "postman-token": "de9f0868-b9cb-4cac-96bc-fa51e8d1e32b",
                "user-agent": "PostmanRuntime/7.15.0",
                "x-forwarded-port": "443"
            },
            "url": "http://info.com/rnaget/projects"
        }, 200)
    elif args[0] == 'http://{}:{}/variants/all'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT0"]):
        return MockResponse(POST_RESPONSES["PLV1"], 200)

    return MockResponse(None, 404)


def mocked_async_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def status_code(self):
            return self.status_code

    if args[0] == 'http://info.com/federation/search':
        return MockResponse({
            "projects": {
                "Umbrella": "Biochemical",
                "Parasol": "Microbial",
                "Umbra": "Chemical"
            },
            "headers": {
                "x-forwarded-proto": "https",
                "host": "postman-echo.com",
                "accept": "*/*",
                "accept-encoding": "gzip, deflate",
                "cache-control": "no-cache",
                "postman-token": "de9f0868-b9cb-4cac-96bc-fa51e8d1e32b",
                "user-agent": "PostmanRuntime/7.15.0",
                "x-forwarded-port": "443"
            },
            "url": "http://info.com/federation/search"
        }, 200)
    elif args[0] == 'http://info2.com/federation/search':
        return MockResponse({"key2": "value2"}, 200)

    return MockResponse(None, 404)


def mocked_peer_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def status_code(self):
            return self.status_code

        def result(self):
            return MockResponse(self.json_data, self.status_code)

    print("ARGS: {}".format(args))
    print("KWARGS: {}".format(kwargs))

    if args[0] == 'http://{}:{}/federation/search'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT0"]):
        return MockResponse({"results": {
            "projects": {
                "Umbrella": "Biochemical",
                "Parasol": "Microbial",
                "Umbra": "Chemical"
            },
            "status": 200}
        }, 200)
    elif args[0] == 'http://{}:{}/federation/search'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT1"]):
        return MockResponse({"results": {"key2": "value2"}, "status": 200}, 200)

    return MockResponse(None, 404)


def mocked_peer_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def status_code(self):
            return self.status_code

        def result(self):
            return MockResponse(self.json_data, self.status_code)

    if args[0] == 'http://{}:{}/federation/search'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT0"]):
        return MockResponse(
            POST_RESPONSES["PLV1"], 200)
    elif args[0] == 'http://{}:{}/federation/search'.format(TESTING_PARAMS["URI"], TESTING_PARAMS["PORT1"]):
        return MockResponse(
            POST_RESPONSES["PLV2"], 200)

    return MockResponse(None, 404)

###################
# Testing Portion #
###################

@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_requests_get)
def test_basic_localresponse_get(mock_requests, client):
    with client:
        args = {
            "endpoint_path": "rnaget/projects",
            "endpoint_payload": ""
        }
        FR = FederationResponse('GET', args, "http://10.9.208.132:8890", "application/json", {})

        FR.handle_local_request()

        RO = FR.get_response_object()

        assert RO["status"] == [200]

        assert RO["results"] == [{
            "projects": {
                "Umbrella": "Biochemical",
                "Parasol": "Microbial",
                "Umbra": "Chemical"
            }}]


@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_requests_get)
def test_invalid_url_localresponse_get(mock_requests, client):
    with client:
        args = {
            "endpoint_path": "rnaget/projects",
            "endpoint_payload": ""
        }
        FR = FederationResponse('GET', args, "http://io.com", "application/json", {})

        FR.handle_local_request()

        RO = FR.get_response_object()

        assert RO["status"] == [404]

        assert RO["results"] == []


@patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_async_requests_get)
def test_async_requests_two_peers_get(mock_requests, client):
    with client:
        args = {
            "endpoint_path": "rnaget/projects",
            "endpoint_payload": ""
        }
        FR = FederationResponse('GET', args, "http://info.com", "application/json", {})

        resp = FR.async_requests(["http://info.com", "http://info2.com"], 'GET', {})

        assert resp[0].json()["projects"] == {
            "Umbrella": "Biochemical",
            "Parasol": "Microbial",
            "Umbra": "Chemical"
        }
        assert resp[1].json() == {"key2": "value2"}


"""
This test focuses on the output from FederationResponse.handle_peer_request(). To efficiently test it, the response
from from async_requests will be mocked to resemble the expected output from FederationResponse.handleLocalRequest().
"""


@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_requests_get)
@patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_peer_requests_get)
def test_valid_PeerRequest_one_peer_get(mock_requests, mock_session, client):
    with client:
        args = {
            "endpoint_path": "rnaget/projects",
            "endpoint_payload": ""
        }
        FR = FederationResponse('GET', args, "http://10.9.208.132:8890", "application/json", {})
        FR.handle_local_request()
        resp = FR.handle_peer_request()
        RO = FR.get_response_object()

        assert RO["results"] == [{
            "projects": {
                "Umbrella": "Biochemical",
                "Parasol": "Microbial",
                "Umbra": "Chemical"
            }},
            {"key2": "value2"}]


"""
This test will focus on the operations.get_search() function. A valid GET query will be sent to be federated. Both
FederationResponse.handleLocalRequest() and FederationResponse.handle_peer_request() will be rerouted to mocked services
to retrieve data
"""


@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_requests_get)
@patch('candig_federation.api.federation.FuturesSession.get', side_effect=mocked_peer_requests_get)
def test_valid_federated_query_one_peer_get(mock_requests, mock_session, client):

    headerObj = Headers()

    headerObj.add('content-type', 'application/json')
    headerObj.add('accept', 'application/json')
    headerObj.add('federation', "True")

    with client:
        with APP.app.test_request_context(
            data={}, headers=headerObj
        ):
            args = {
                "endpoint_path": "rnaget/projects",
                "endpoint_payload": ""
            }
            RO = operations.get_search(args["endpoint_path"], args["endpoint_payload"])

            assert RO["results"] == [{
                "projects": {
                    "Umbrella": "Biochemical",
                    "Parasol": "Microbial",
                    "Umbra": "Chemical"
                }},
                {"key2": "value2"}]


@patch('candig_federation.api.federation.requests.Session.post', side_effect=mocked_requests_post)
@patch('candig_federation.api.federation.FuturesSession.post', side_effect=mocked_peer_requests_post)
def test_valid_PeerRequest_one_peer_post(mock_session, mock_requests,  client):
    with client:
        args = {
            "endpoint_path": "variants/all",
            "endpoint_payload": ""
        }
        FR = FederationResponse('POST', args, "http://10.9.208.132:8890", "application/json", {})
        FR.handle_local_request()
        PR = FR.handle_peer_request()
        RO = FR.get_response_object()

        assert RO["results"] == [POST_RESPONSES["PLV1"], POST_RESPONSES["PLV2"]]


@patch('candig_federation.api.federation.FuturesSession.post', side_effect=mocked_peer_requests_post)
def test_valid_PeerRequest_no_local_one_peer_post(mock_session,  client):
    with client:
        args = {
            "endpoint_path": "variants/all",
            "endpoint_payload": ""
        }
        FR = FederationResponse('POST', args, "http://10.9.208.132:8890", "application/json", {})
        FR.handle_local_request()
        PR = FR.handle_peer_request()
        RO = FR.get_response_object()



        assert RO["results"] == POST_RESPONSES["PLV2"]