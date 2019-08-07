from unittest.mock import Mock, patch

from nose.tools import assert_is_not_none

import sys
import os

import pytest

sys.path.append("{}/{}".format(os.getcwd(), "candig_federation"))

sys.path.append(os.getcwd())

from candig_federation.__main__ import app
from candig_federation.api import operations
from candig_federation.api.federation import FederationResponse


@pytest.fixture()
def client():

    context = app.app.app_context()

    return context


@patch('candig_federation.api.federation.FederationResponse.handleLocalRequest')
def test_basic_localresponse(mock_handleLocalRequest, client):

    projects = {
        "projects": {
            "Chevron": "Chemical",
            "Nestle": "Microbial",
            "Garmin": "Mechanical"
        }}

    mock_handleLocalRequest.return_value = [200, projects]

    with client:
        args = {
            "endpoint_path": "get/Testing",
            "endpoint_payload": ""
        }
        FR = FederationResponse('GET', args, "l", "o", "lw", {})

        code, results = FR.handleLocalRequest()

        print(code, results)

        assert code == 200


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

    if args[0] == 'http://info.com/rnaget/projects':
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
    elif args[0] == 'http://someotherurl.com/anothertest.json':
        return MockResponse({"key2": "value2"}, 200)

    return MockResponse(None, 404)


@patch('candig_federation.api.federation.requests.Session.get', side_effect=mocked_requests_get)
def test_basic_localresponse_get(mock_requests, client):
    with client:
        args = {
            "endpoint_path": "rnaget/projects",
            "endpoint_payload": ""
        }
        FR = FederationResponse('GET', args, "http://info.com", "0.0.0.0", "application/json", {})

        FR.handleLocalRequest()

        RO = FR.getResponseObject()

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
        FR = FederationResponse('GET', args, "http://io.com", "0.0.0.0", "application/json", {})

        FR.handleLocalRequest()

        RO = FR.getResponseObject()

        assert RO["status"] == [404]

        assert RO["results"] == []