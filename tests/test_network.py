"""
Test suite to check for errors upon federation_service start up
"""


import sys
import os
import logging

import pytest

sys.path.append("{}/{}".format(os.getcwd(), "candig_federation"))

sys.path.append(os.getcwd())

from candig_federation.api import network
from jsonschema.exceptions import ValidationError

VALID_SERVERS = "./tests/test_data/servers.json"
INVALID_SERVER_VAL = "./tests/test_data/servers_bad_value.json"
INVALID_SERVER_KEY = "./tests/test_data/servers_bad_initkey.json"

VALID_SCHEMA = "./tests/test_data/schemas.json"
INVALID_SCHEMA = "notschemas"


def test_invalid_schema_location_getSchemaDict_exception():
    with pytest.raises(FileNotFoundError):
        network.get_schema_dict(INVALID_SCHEMA)

def test_invalid_schema_location_getSchemaDict_exit():
    with pytest.raises(SystemExit):
        network.get_schema_dict(INVALID_SCHEMA, logging.getLogger("Test"))

def test_invalid_schema_type_parseConfigs():
    with pytest.raises(KeyError):
        network.parse_configs("wrong", VALID_SERVERS, VALID_SCHEMA)

def test_invalid_file_path_parseConfigs():
    with pytest.raises(FileNotFoundError):
        network.parse_configs("servers", "blank", VALID_SCHEMA)

def test_invalid_schema_format_value_parseConfigs():
    with pytest.raises(ValidationError):
        network.parse_configs("servers", INVALID_SERVER_VAL, VALID_SCHEMA)

def test_invalid_schema_format_initkey_parseConfigs():
    with pytest.raises(KeyError):
        network.parse_configs("servers", INVALID_SERVER_KEY, VALID_SCHEMA)

def test_invalid_schema_type_parseConfigs_exit():
    with pytest.raises(SystemExit):
        network.parse_configs("wrong", VALID_SERVERS, VALID_SCHEMA, logging.getLogger("Test"))

def test_invalid_file_path_parseConfigs_exit():
    with pytest.raises(SystemExit):
        network.parse_configs("servers", "blank", VALID_SCHEMA, logging.getLogger("Test"))

def test_invalid_schema_format_value_parseConfigs_exit():
    with pytest.raises(SystemExit):
        network.parse_configs("servers", INVALID_SERVER_VAL, VALID_SCHEMA, logging.getLogger("Test"))

def test_invalid_schema_format_initkey_parseConfigs_exit():
    with pytest.raises(SystemExit):
        network.parse_configs("servers", INVALID_SERVER_KEY, VALID_SCHEMA, logging.getLogger("Test"))

def test_valid_schema_location_getSchemaDict():
    schema_dict = network.get_schema_dict(VALID_SCHEMA)
    assert [*schema_dict] == ['servers', 'services']

def test_valid_schema_parseConfigs():
    servers = network.parse_configs("servers", VALID_SERVERS, VALID_SCHEMA)
    assert servers["p1"] == "http://10.9.208.132:8890"