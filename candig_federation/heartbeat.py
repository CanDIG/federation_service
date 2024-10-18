#!/usr/bin/env python3
import time
from network import get_registered_servers
import requests
import os.path
import os

def check_pulse():
    servers = get_registered_servers()
    if len(servers) == 0:
        return
    # Determine which sites we have access to
    live_servers = []
    log = ""
    for server in servers.values():
        if server['server']['id'] != os.getenv("FEDERATION_SELF_SERVER_ID", 'internal-1'):
            try:
                url = f"{server['server']['url']}/hello"
                log += f"\ntesting {url}"
                service_info = requests.get(url, timeout=2)
                if service_info.ok:
                    live_servers.append(server['server']['id'])
            except Exception as e:
                log += "\n" + str(e)
        else:
            live_servers.append(server['server']['id'])


    # Determine whether or not those sites are available by pinging Federation service-info
    with open('/app/federation/live_servers.txt', 'w') as f:
        f.write("|".join(live_servers))

    with open('/app/federation/log.txt', 'w') as f:
        f.write(log)


def get_live_servers():
    live_servers = []
    if os.path.isfile("/app/federation/live_servers.txt"):
        with open('/app/federation/live_servers.txt', 'r') as f:
            live_servers_str = f.read().strip()
            live_servers = live_servers_str.split('|')
    return live_servers

if __name__ == "__main__":
    while(True):
        check_pulse()
        time.sleep(30)
