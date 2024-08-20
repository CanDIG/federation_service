#!/usr/bin/env python3
import time
from network import get_registered_servers
import requests
import os.path

def check_pulse():
    servers = get_registered_servers()
    # Determine which sites we have access to
    live_servers = []
    log = ""
    try:
        for server in servers.values():
            url = f"{server['server']['url']}/v1/service-info"
            log += f"\ntesting {url}"
            service_info = requests.get(url, timeout=2)
            if service_info.ok:
                live_servers.append(server['server']['id'])

        # Determine whether or not those sites are available by pinging Federation service-info
        with open('/app/federation/live_servers.txt', 'w') as f:
            f.write("|".join(live_servers))
    except Exception as e:
        log += "\n" + str(e)

    with open('/app/federation/log.txt', 'w') as f:
        f.write(log)
        f.write(str(e))


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
