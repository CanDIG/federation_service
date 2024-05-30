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

from server import main
from federation import FederationResponse
import operations
from tests.test_data.test_structs import *

APP = main()

REPO_DIR = os.path.abspath(f"{os.path.dirname(os.path.realpath(__file__))}/..")
sys.path.insert(0, os.path.abspath(f"{REPO_DIR}"))
sys.path.insert(0, os.path.abspath(f"{REPO_DIR}/candig_federation"))
import operations

CANDIG_URL = os.getenv("CANDIG_URL", "http://localhost")
VAULT_URL = os.getenv("VAULT_URL", "http://localhost")


@pytest.fixture(autouse=True)
def services(requests_mock):
    with open(os.path.abspath("tests/test_data/services.json")) as f:
        services = {"services": json.load(f)}
        requests_mock.get(f"{VAULT_URL}/v1/federation/services", json={"data": services}, status_code=200)
    requests_mock.post(f"{VAULT_URL}/v1/auth/approle/role/federation/secret-id", json={"data": {"secret_id": "gsfsf"}}, status_code=200)
    requests_mock.post(f"{VAULT_URL}/v1/auth/approle/login", json={"auth": {"client_token": "gsfsf"}}, status_code=200)


@pytest.fixture()
def two_servers(requests_mock):
    with open(os.path.abspath("tests/test_data/two_servers.json")) as f:
        servers = {"servers": json.load(f)}
        requests_mock.get(f"{VAULT_URL}/v1/federation/servers", json={"data": servers}, status_code=200)
    requests_mock.post(f"{VAULT_URL}/v1/auth/approle/role/federation/secret-id", json={"data": {"secret_id": "gsfsf"}}, status_code=200)
    requests_mock.post(f"{VAULT_URL}/v1/auth/approle/login", json={"auth": {"client_token": "gsfsf"}}, status_code=200)


@pytest.fixture()
def three_servers(requests_mock):
    with open(os.path.abspath("tests/test_data/three_servers.json")) as f:
        servers = {"servers": json.load(f)}
        requests_mock.get(f"{VAULT_URL}/v1/federation/servers", json={"data": servers}, status_code=200)
    requests_mock.post(f"{VAULT_URL}/v1/auth/approle/role/federation/secret-id", json={"data": {"secret_id": "gsfsf"}}, status_code=200)
    requests_mock.post(f"{VAULT_URL}/v1/auth/approle/login", json={"auth": {"client_token": "gsfsf"}}, status_code=200)


@pytest.fixture()
def client(services):
    context = APP.app.app_context()

    return context

def get_federation_response(request_type, headers="Headers"):

    return FederationResponse(
                        request=request_type,
                        endpoint_payload="",
                        endpoint_path=TestParams["path"],
                        request_dict=TestParams[headers],
                        endpoint_service=TestParams["service"])



# Taken from https://stackoverflow.com/questions/15753390/how-can-i-mock-requests-and-the-response
def mocked_service_get(*args, **kwargs):
    if args[0] == 'http://{}:{}/rnaget/projects'.format(TestParams["URI"], TestParams["PORT0"]):
        return GetResponse["s1"]
    if args[0] == 'http://{}:{}/rnaget/projects'.format(TestParams["URI"], TestParams["PORT1"]):
        return GetResponse["s2"]
    if args[0] == 'http://{}:{}/rnaget/projects'.format(TestParams["URI"], TestParams["PORT2"]):
        return GetResponse["s3"]

    return GetResponse["fail"]


def mocked_service_post(*args, **kwargs):
    if args[0] == 'http://{}:{}/rnaget/projects'.format(TestParams["URI"], TestParams["PORT0"]):
        return PostResponse["PLV1"]
    if args[0] == 'http://{}:{}/rnaget/projects'.format(TestParams["URI"], TestParams["PORT1"]):
        return PostResponse["PLV2"]
    if args[0] == 'http://{}:{}/rnaget/projects'.format(TestParams["URI"], TestParams["PORT2"]):
        return PostResponse["PLV3"]

    return GetResponse["fail"]


# The returns from async requests need to be futures, so a second class is used to represent that

def mocked_async_requests_get(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return GetResponse["i1"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return GetResponse["i2"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return GetResponse["i3"]

    return GetResponse["fail"]


def mocked_async_requests_post(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return PostResponse["iPLV1"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return PostResponse["iPLV2"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return PostResponse["iPLV3"]

    return GetResponse["fail"]

# Mocked async requests that simulate "server" node failing (Timeout)

def mocked_async_p1_timeout_requests_get(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return GetResponse["i1"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return GetResponse["timeout"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return GetResponse["i3"]

    return GetResponse["fail"]


def mocked_async_p1_timeout_requests_post(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return PostResponse["iPLV1"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return GetResponse["timeout"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return PostResponse["iPLV3"]

    return GetResponse["fail"]


# Mocked async requests that simulate "local" node failing (Timeout)

def mocked_async_local_timeout_requests_get(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return GetResponse["timeout"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return GetResponse["i2"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return GetResponse["i3"]

    return GetResponse["fail"]


def mocked_async_local_timeout_requests_post(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return PostResponse["timeout"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return PostResponse["iPLV2"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return PostResponse["iPLV3"]

    return GetResponse["fail"]


# Mocked async requests that simulate "server" node failing (Connection Error)

def mocked_async_p1_ConnErr_requests_get(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return GetResponse["i1"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return GetResponse["fail"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return GetResponse["i3"]

    return GetResponse["fail"]


def mocked_async_p1_ConnErr_requests_post(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return PostResponse["iPLV1"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return PostResponse["fail"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return PostResponse["iPLV3"]

    return GetResponse["fail"]


# Mocked async requests that simulate "local" node failing (Connection Error)

def mocked_async_local_ConnErr_requests_get(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return GetResponse["fail"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return GetResponse["i2"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return GetResponse["i3"]

    return GetResponse["fail"]


def mocked_async_local_ConnErr_requests_post(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return PostResponse["fail"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return PostResponse["iPLV2"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return PostResponse["iPLV3"]

    return GetResponse["fail"]

# Mocked async requests that simulate "local" node failing (Connection Error) and one server TimeOut

def mocked_async_local_ConnErr_p1_Timeout_requests_get(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return GetResponse["fail"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return GetResponse["timeout"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return GetResponse["i3"]

    return GetResponse["fail"]


def mocked_async_local_ConnErr_p1_Timeout_requests_post(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return GetResponse["fail"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return GetResponse["timeout"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return PostResponse["iPLV3"]

    return GetResponse["fail"]

# Mocked async requests that simulate "local" node failing (TimeOut) and one server TimeOut

def mocked_async_local_TimeOut_p1_Timeout_requests_get(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return GetResponse["timeout"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return GetResponse["timeout"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return GetResponse["i3"]

    return GetResponse["fail"]


def mocked_async_local_TimeOUt_p1_Timeout_requests_post(*args, **kwargs):
    if args[0] == 'http://{}'.format(TestParams["Tyk1"]):
        return GetResponse["timeout"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk2"]):
        return GetResponse["timeout"]
    elif args[0] == 'http://{}'.format(TestParams["Tyk3"]):
        return PostResponse["iPLV3"]

    return GetResponse["fail"]



###################
# Testing Portion #
###################

# Test basic service requests --------------------------------------------------------------------

@patch('federation.requests.Session.get', side_effect=mocked_service_get)
def test_valid_noFed_get(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("GET")
        RO, Status = FR.get_response_object()

        assert RO["status"] == 200
        assert RO["results"] == GetResponse["j1"]


@patch('federation.requests.Session.post', side_effect=mocked_service_post)
def test_valid_noFed_post(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("POST")
        RO, Status = FR.get_response_object()
        assert RO["status"] == 200
        assert RO["results"] == PostListV1

# Test basic service errors --------------------------------------------------------------------

@patch('federation.requests.Session.get', side_effect=exceptions.ConnectionError)
def test_invalid_noFed_get(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("GET")
        RO, Status = FR.get_response_object()
        assert RO["status"] == 404
        assert RO["results"] == {}


@patch('federation.requests.Session.post', side_effect=exceptions.ConnectionError)
def test_invalid_noFed_post(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("POST")
        RO, Status = FR.get_response_object()
        assert RO["status"] == 404
        assert RO["results"] == {}


@patch('federation.requests.Session.get', side_effect=exceptions.Timeout)
def test_timeout_noFed_get(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("GET")
        RO, Status = FR.get_response_object()
        assert RO["status"] == 504
        assert RO["results"] == {}


@patch('federation.requests.Session.post', side_effect=exceptions.Timeout)
def test_timeout_noFed_post(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("POST")
        RO, Status = FR.get_response_object()
        assert RO["status"] == 504
        assert RO["results"] == {}

# Test the async request function --------------------------------------------------------------------

@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_get)
def test_valid_asyncRequests_two_servers_get(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("POST", "Federate")
        resp = FR.async_requests(request='GET',
                                 endpoint_path=TestParams["path"],
                                 endpoint_payload="",
                                 header=TestParams["Headers"],
                                 endpoint_service=TestParams["service"])
        resp = [r["response"] for r in resp.values()]
        Success = list(filter(lambda x: x == 200, map(lambda a: a.status_code, resp)))

        assert len(resp) == 2
        assert Success == [200, 200]


@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_post)
def test_valid_asyncRequests_two_servers_post(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("POST")
        resp = FR.async_requests(request='POST',
                                 endpoint_path=TestParams["path"],
                                 endpoint_payload="",
                                 header=TestParams["Headers"],
                                 endpoint_service=TestParams["service"])
        resp = [r["response"] for r in resp.values()]
        Success = list(filter(lambda x: x == 200, map(lambda a: a.status_code, resp)))

        assert len(resp) == 2
        assert Success == [200, 200]


@patch('federation.FuturesSession.post', side_effect=exceptions.ConnectionError)
def test_invalid_asyncRequests_two_servers_get(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("POST")
        resp = FR.async_requests(request='GET',
                                 endpoint_path=TestParams["path"],
                                 endpoint_payload="",
                                 header=TestParams["Headers"],
                                 endpoint_service=TestParams["service"])
        ConnErrs = list(map(lambda a: "ConnectionError" in str(a), resp.values()))

        # Error should just be propagated through since handle_server_request will address it

        assert len(resp) == 2
        assert ConnErrs == [True, True]


@patch('federation.FuturesSession.post', side_effect=exceptions.ConnectionError)
def test_invalid_asyncRequests_two_servers_post(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("POST")
        resp = FR.async_requests(request='POST',
                                 endpoint_path=TestParams["path"],
                                 endpoint_payload="",
                                 header=TestParams["Headers"],
                                 endpoint_service=TestParams["service"])

        Success = list(map(lambda a: "ConnectionError" in str(a), resp.values()))

        assert len(resp) == 2
        assert Success == [True, True]


@patch('federation.FuturesSession.post', side_effect=exceptions.Timeout)
def test_timeout_asyncRequests_two_servers_post(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("POST")
        resp = FR.async_requests(request='POST',
                                 endpoint_path=TestParams["path"],
                                 endpoint_payload="",
                                 header=TestParams["Headers"],
                                 endpoint_service=TestParams["service"])

        Success = list(map(lambda a: "Timeout" in str(a), resp.values()))

        assert len(resp) == 2
        assert Success == [True, True]


@patch('federation.FuturesSession.post', side_effect=exceptions.Timeout)
def test_timeout_asyncRequests_two_servers_get(mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("GET")
        resp = FR.async_requests(request='GET',
                                 endpoint_path=TestParams["path"],
                                 endpoint_payload="",
                                 header=TestParams["Headers"],
                                 endpoint_service=TestParams["service"])

        TimeoutErrs = list(map(lambda a: "Timeout" in str(a), resp.values()))

        # Error should just be propagated through since handle_server_request will address it

        assert len(resp) == 2
        assert TimeoutErrs == [True, True]

# Test Federation with one server --------------------------------------------------------------------

@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_get)
def test_valid_ServerRequest_one_server_get(mock_requests, mock_session, client, two_servers):
    with client:
        FR = get_federation_response("GET", "Federate")
        RO, Status = FR.get_response_object()
        assert Status == 200
        for server in RO:
            loc = server["location"]["name"]
            assert server["results"] == GetResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_get)
def test_valid_federated_query_one_server_get(mock_requests, mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]
                }),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                assert server["results"] == GetResponse[loc]['results']


@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_post)
def test_valid_ServerRequest_one_server_post(mock_session, mock_requests, client, two_servers):
    with client:
        FR = get_federation_response("POST", "Federate")
        RO, Status = FR.get_response_object()

        assert Status == 200
        for server in RO:
            loc = server["location"]["name"]
            assert server["results"] == PostResponse[loc]['results']


@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_post)
def test_valid_federated_query_one_server_post(mock_requests, mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server['results'] == PostResponse[loc]['results']


# Test Federation with one server, have "local" error -------------------------------------------------

@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_ConnErr_requests_post)
def test_valid_federated_local_ConnErr_one_server_post(mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server['results'] == PostResponse[loc]['results']


@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_timeout_requests_post)
def test_valid_federated_local_TimeOut_one_server_post(mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    if server["status"] == 200:
                        assert server['results'] == PostResponse[loc]['results']



@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_timeout_requests_get)
def test_valid_federated_local_TimeOut_one_server_get(mock_requests, mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == GetResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_ConnErr_requests_get)
def test_valid_federated_local_ConnErr_one_server_get(mock_requests, mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path"   : TestParams["path"],
                                 "payload": "",
                                 "method"    : "GET",
                                 "service": TestParams["service"]
                                 }),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == GetResponse[loc]['results']


# Test Federation with one server, have server error out --------------------------------------------------

@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_p1_ConnErr_requests_post)
def test_ConnErr_federated_valid_local_one_server_post(mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == PostResponse[loc]['results']

@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_p1_timeout_requests_post)
def test_TimeOut_federated_valid_local_one_server_post(mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == PostResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_p1_ConnErr_requests_get)
def test_ConnErr_federated_valid_local_one_server_get(mock_requests, mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == GetResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_p1_ConnErr_requests_get)
def test_TimeOut_federated_valid_local_one_server_get(mock_requests, mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == GetResponse[loc]['results']

# Test Federation with two nodes and local -----------------------------------------------------


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_get)
def test_valid_ServerRequest_two_server_get(mock_requests, mock_session, client, three_servers):
    with client:
        FR = get_federation_response("GET", "Federate")
        RO, Status = FR.get_response_object()

        assert Status == 200
        for server in RO:
            loc = server["location"]["name"]
            if server["status"] == 200:
                assert server["results"] == GetResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_get)
def test_valid_federated_query_two_server_get(mock_requests, mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == GetResponse[loc]['results']


@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_post)
def test_valid_ServerRequest_two_server_post(mock_session, mock_requests, client, three_servers):
    with client:
        FR = get_federation_response("POST", "Federate")
        RO, Status = FR.get_response_object()

        assert Status == 200
        for server in RO:
            loc = server["location"]["name"]
            if server["status"] == 200:
                assert server["results"] == PostResponse[loc]['results']


@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_post)
def test_valid_federated_query_two_server_post(mock_requests, mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == PostResponse[loc]['results']


# Test Federation with two nodes and local error -----------------------------------------------------

@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_ConnErr_requests_post)
def test_valid_federated_local_ConnErr_two_server_post(mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == PostResponse[loc]['results']


@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_timeout_requests_post)
def test_valid_federated_local_TimeOut_two_server_post(mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == PostResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_ConnErr_requests_get)
def test_valid_federated_local_ConnErr_two_server_get(mock_requests, mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == GetResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_timeout_requests_get)
def test_valid_federated_local_TimeOut_two_server_get(mock_requests, mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == GetResponse[loc]['results']


# Test Federation with two nodes (One timeout) and local Error -----------------------------------------------------

@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_ConnErr_p1_Timeout_requests_post)
def test_one_TimeOut_federated_local_ConnErr_two_server_post(mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == PostResponse[loc]['results']


@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_TimeOUt_p1_Timeout_requests_post)
def test_one_TimeOut_federated_local_TimeOut_two_server_post(mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == PostResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_ConnErr_p1_Timeout_requests_get)
def test_one_TimeOut_federated_local_ConnErr_two_server_get(mock_requests, mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == GetResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_local_TimeOut_p1_Timeout_requests_get)
def test_one_TimeOut_federated_local_TimeOut_two_server_get(mock_requests, mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == GetResponse[loc]['results']


# Test Federation with two nodes (One timeout) and local valid -----------------------------------------------------

@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_p1_timeout_requests_post)
def test_one_TimeOut_federated_valid_two_server_post(mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == PostResponse[loc]['results']


@patch('federation.requests.Session.post', side_effect=mocked_service_post)
@patch('federation.FuturesSession.post', side_effect=mocked_async_p1_timeout_requests_post)
def test_one_TimeOut_federated_local_valid_two_server_post(mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "POST",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == PostResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_p1_timeout_requests_get)
def test_one_TimeOut_federated_local_valid_two_server_get(mock_requests, mock_session, client, three_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": TestParams["path"],
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]}),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 200
            for server in RO:
                loc = server["location"]["name"]
                if server["status"] == 200:
                    assert server["results"] == GetResponse[loc]['results']


@patch('federation.requests.Session.get', side_effect=mocked_service_get)
@patch('federation.FuturesSession.post', side_effect=mocked_async_requests_get)
def test_invalid_backslash_endpoint_start(mock_requests, mock_session, client, two_servers):
    with client:
        with APP.app.test_request_context(
                data=json.dumps({"path": "/fail/this/path",
                                 "payload": "",
                                 "method": "GET",
                                 "service": TestParams["service"]
                }),
                headers=Headers(fedHeader.headers)
        ):
            RO, Status = operations.post_search()

            assert Status == 400

