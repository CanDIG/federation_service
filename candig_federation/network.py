"""
Methods to handle services and peer servers
"""

import json
from flask import current_app
import authz


def get_registered_servers():
    try:
        with open(current_app.config['server_file']) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error in get_registered_servers: {type(e)} {str(e)}")
        return None



def register_server(obj):
    servers = get_registered_servers()
    new_server = obj['server']
    if servers is not None:
        # check to see if it's already here:
        found = False
        for s in servers.values():
            if json.dumps(s, sort_keys=True) == json.dumps(new_server, sort_keys=True):
                found = True
        if found:
            return None
        servers[new_server['id']] = new_server

    if 'testing' in obj['authentication']:
        new_server['testing'] = True
    else:
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

    try:
        with open(current_app.config['server_file'], 'w') as f:
            f.write(json.dumps(servers))
    except Exception as e:
        print(f"Error in register_server: {type(e)} {str(e)}")
        return None
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
    try:
        with open(current_app.config['service_file']) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error in get_registered_services: {type(e)} {str(e)}")
        return None


def register_service(obj):
    services = get_registered_services()
    if services is not None:
        services[obj['id']] = obj
    try:
        with open(current_app.config['service_file'], 'w') as f:
            f.write(json.dumps(services))
    except Exception as e:
        print(f"Error in register_service: {type(e)} {str(e)}")
        return None
    return obj


def unregister_service(service_id):
    services = get_registered_services()
    result = None
    if services is not None and service_id in services:
        result = services.pop(service_id)
        with open(current_app.config['service_file'], 'w') as f:
            f.write(json.dumps(services))
    return result
