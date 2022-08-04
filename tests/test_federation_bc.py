"""
These integration tests are skipped during CI since they test API responses 
from peer servers that are run locally. If you want to run these, start two 
uwsgi federation instances in different ports following the instructions on 
the README and update the fixtures with your own URL and ports.
"""

import json

import pytest
import requests

from tests.test_data.test_structs import katsu

def sort_dict(dict):
    """
    Sort dictionaries alphabetically by keys.
    """
    sorted_keys = sorted(dict.keys())
    sorted_dict = {key: dict[key] for key in sorted_keys}
    return sorted_dict

@pytest.fixture
def url():
    return "http://ga4ghdev01.bcgsc.ca"

@pytest.fixture
def ports():
    return ["8891", "8892"]

## Tests Start Here

def test_servers(url, ports):
    """
    Test peer server URLs are returned properly.
    """
    r1 = requests.get(f"{url}:{ports[0]}/federation/servers")
    r2 = requests.get(f"{url}:{ports[1]}/federation/servers")
    with open("./configs/servers.json") as j:
        j = json.load(j)
    
    assert sort_dict(r1.json()) == sort_dict(r2.json()), \
           "Peer servers should be the same in every instance"
    assert sort_dict(r1.json()) == sort_dict(r2.json()) == sort_dict(j["servers"]), \
           "The returned server URLs don't match servers.json"


def test_services(url, ports):
    """Test services URLs are returned properly."""
    r1 = requests.get(f"{url}:{ports[0]}/federation/services")
    r2 = requests.get(f"{url}:{ports[1]}/federation/services")
    with open("./configs/services.json") as j:
        j = json.load(j)
    
    assert sort_dict(r1.json()) == sort_dict(r2.json()), \
           "Services should be the same in every instance"
    assert sort_dict(r1.json()) == sort_dict(r2.json()) == sort_dict(j["services"]), \
           "The response's service URLs don't match services.json"


def test_search(url, ports):
    """
    Test unfederated query (single node).
    """
    url = f"{url}:{ports[0]}/federation/search"
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
    r = requests.post(url, headers=headers, json=payload)
    assert r.json() == katsu