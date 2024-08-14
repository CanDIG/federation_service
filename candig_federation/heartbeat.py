#!/usr/bin/env python3
import time
from network import get_registered_servers, get_registered_services
from requests_futures.sessions import FuturesSession

def check_pulse():
    servers = get_registered_servers()
    # Determine which sites we have access to
    live_services = []
    async_session = FuturesSession(max_workers=10)  # capping max threads
    for server in servers.values():
        url = f"{server['server']['url']}/v1/service-info"
        service_info = async_session.post(url, timeout=1)
        if service_info.ok:
            live_services.append(server['server']['id'])

    # Determine whether or not those sites are available by pinging Federation service-info
    with open('./live_services.txt', 'w') as f:
        f.write("|".join(live_services))


def get_live_services():
    live_services = []
    with open('./live_services.txt', 'r') as f:
        live_services_str = f.read()
        live_services = live_services_str.split('|')
    return live_services

if __name__ == "__main__":
    while(True):
        check_pulse()
        time.sleep(30)
