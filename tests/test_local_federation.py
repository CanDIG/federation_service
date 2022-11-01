"""
These integration tests are skipped during CI since they test API responses
from peer servers that are run locally. If you want to run these, start two
uwsgi federation instances in different ports following the instructions on
the README and update the fixtures with your own URL and ports. The tests 
are set up to work with two nodes, but you can modify the code to add more.
"""

import json
import os

import pytest
import requests

# Skip tests in this module when running in Travis CI
pytestmark = pytest.mark.skipif(os.environ.get("TRAVIS") == "true",
                                reason="These integration tests only run with local instances running (not CI server).")

# Update these fixtures with your own server address/ports
@ pytest.fixture
def server():
    return "http://ga4ghdev01.bcgsc.ca"


@ pytest.fixture
def ports():
    return ["8891", "8892"]


def sort_dict(dict):
    """
    Sort dictionaries alphabetically by keys.
    """
    sorted_keys = sorted(dict.keys())
    return {key: dict[key] for key in sorted_keys}


# Tests Start Here
def test_servers(server, ports):
    """
    Test peer server URLs are returned properly.
    """
    r1 = requests.get(f"{server}:{ports[0]}/federation/servers")
    r2 = requests.get(f"{server}:{ports[1]}/federation/servers")
    with open("./configs/servers.json") as j:
        j = json.load(j)
        servers = j["servers"]

    assert r1.json() == r2.json() == servers, \
        "The returned server URLs don't match servers.json"


def test_services(server, ports):
    """
    Test service URLs are returned properly.
    """
    r1 = requests.get(f"{server}:{ports[0]}/federation/services")
    r2 = requests.get(f"{server}:{ports[1]}/federation/services")
    with open("./configs/services.json") as j:
        j = json.load(j)
        services = j["services"]

    assert sort_dict(r1.json()) == sort_dict(r2.json()) == sort_dict(services), \
        "The returned service URLs don't match services.json"


def test_search(server, ports):
    """
    Test unfederated and federated queries.
    """
    r = []  # Responses
    headers = {
        "content-type": "application/json",
        "federation": "false"
    }
    payload = {
        "request_type": "GET",
        "endpoint_path": "api/datasets",
        "endpoint_payload": {},
        "endpoint_service": "katsu"
    }
    r1 = requests.post(f"{server}:{ports[0]}/federation/search",
                       headers=headers, json=payload)
    r2 = requests.post(f"{server}:{ports[1]}/federation/search",
                       headers=headers, json=payload)

    # Test unfederated queries
    assert r1.json()["service"] == r2.json()["service"] == "katsu", \
        "The returned service doesn't match the request."
    assert r1.json()["status"] == r2.json()["status"] == 200, \
        "The request wasn't successful."

    # Test federated queries
    headers["federation"] = "true"
    headers["authorization"] = "\"Bearer\" + token.json()['id_token']"

    r3 = requests.post(f"{server}:{ports[0]}/federation/search",
    headers=headers, json=payload)
    r4 = requests.post(f"{server}:{ports[1]}/federation/search",
    headers=headers, json=payload)

    assert r3.json()["service"] == r4.json()["service"] == "katsu", \
        "The returned service doesn't match the request."
    assert r3.json()["status"] == r4.json()["status"] == 200, \
        "The request wasn't successful."
    assert len(r1.json()['results']) * 2 == len(r3.json()['results']), \
        "Federated results should be double of the unfederated results."
