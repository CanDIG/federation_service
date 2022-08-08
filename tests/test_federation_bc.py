"""
These integration tests are skipped during CI since they test API responses
from peer servers that are run locally. If you want to run these, start two
uwsgi federation instances in different ports following the instructions on
the README and update the fixtures with your own URL and ports.
"""

import json
import os

import pytest
import requests

from tests.test_data.test_structs import katsu

# Skip tests in this module when running in Travis CI
pytestmark = pytest.mark.skipif(os.environ.get("TRAVIS") == "true",
                                reason="These integration tests only work with local instances running.")

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
    sorted_dict = {key: dict[key] for key in sorted_keys}
    return sorted_dict


# Tests Start Here
def test_servers(server, ports):
    """
    Test peer server URLs are returned properly.
    """
    r1 = requests.get(f"{server}:{ports[0]}/federation/servers")
    r2 = requests.get(f"{server}:{ports[1]}/federation/servers")
    with open("./configs/servers.json") as j:
        j = json.load(j)

    assert sort_dict(r1.json()) == sort_dict(r2.json()), \
        "Peer servers should be the same in every instance"
    assert sort_dict(r1.json()) == sort_dict(r2.json()) == sort_dict(j["servers"]), \
        "The returned server URLs don't match servers.json"


def test_services(server, ports):
    """Test services URLs are returned properly."""
    r1 = requests.get(f"{server}:{ports[0]}/federation/services")
    r2 = requests.get(f"{server}:{ports[1]}/federation/services")
    with open("./configs/services.json") as j:
        j = json.load(j)

    assert sort_dict(r1.json()) == sort_dict(r2.json()), \
        "Services should be the same in every instance"
    assert sort_dict(r1.json()) == sort_dict(r2.json()) == sort_dict(j["services"]), \
        "The returned service URLs don't match services.json"


def test_search(server, ports):
    """
    Test unfederated query (single server).
    """
    r = []  # Responses
    headers = {
        "Content-Type": "application/json",
        "federation": "false"
    }
    payload = {
        "request_type": "GET",
        "endpoint_path": "api/datasets",
        "endpoint_payload": {},
        "endpoint_service": "katsu"
    }
    for port in ports:
        url = f"{server}:{port}/federation/search"
        print(url)
        r.append(requests.post(url, headers=headers, json=payload))
    
    print(r)
    print(r[0].json())
    print(r[1].json())

    assert r[0].json()["service"] == r[1].json()["service"] == "katsu"
    assert r[0].json()["status"] == r[1].json()["status"] == 200
    assert r[0].json() == r[1].json() == katsu
