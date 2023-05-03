"""
Provides parsing methods to initialize the server's peer to peer/service connections.
"""

import os
import json
from flask import current_app
from candig_federation.api import authz


def get_registered_servers():
    with open(current_app.config['server_file']) as f:
        try:
            return json.load(f)
        except Exception as e:
            return None


def register_server(obj):
    servers = get_registered_servers()
    if servers is not None:
        servers[obj['server']['id']] = obj['server']

    try:
        token = obj['authentication']['token']
        issuer = obj['authentication']['issuer']

        authz.add_provider_to_tyk(token, issuer)
    except Exception as e:
        raise Exception(f"Failed to register server with tyk: {type(e)} {str(e)}")
    try:
        authz.add_provider_to_opa(token, issuer)
    except Exception as e:
        raise Exception(f"Failed to register server with opa: {type(e)} {str(e)}")

    with open(current_app.config['server_file'], 'w') as f:
        f.write(json.dumps(servers))
    return obj['server']


def unregister_server(server_id):
    servers = get_registered_servers()
    result = None
    if servers is not None and server_id in servers:
        result = servers.pop(server_id)
        with open(current_app.config['server_file'], 'w') as f:
            f.write(json.dumps(servers))
    return result


def get_registered_services():
    with open(current_app.config['service_file']) as f:
        try:
            return json.load(f)
        except Exception as e:
            return None


def register_service(obj):
    services = get_registered_services()
    if services is not None:
        services[obj['id']] = obj
    with open(current_app.config['service_file'], 'w') as f:
        f.write(json.dumps(services))
    return obj


def unregister_service(service_id):
    services = get_registered_services()
    result = None
    if services is not None and service_id in services:
        result = services.pop(service_id)
        with open(current_app.config['service_file'], 'w') as f:
            f.write(json.dumps(services))
    return result
