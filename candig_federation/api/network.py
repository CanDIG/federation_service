"""
Provides methods to initialize the server's peer to peer connections.
"""

import os
import requests
import json


def getInitialPeerList(filePath, logger=None):
    """
    Attempts to get a list of peers from a file specified in configuration.
    This file has one URL per line and can contain newlines and comments.

        # Local intranet peer
        https://192.168.1.1

    The server will attempt to add URLs in this file to its registry at
    startup and will log a warning if the file isn't found.
    """
    ret = []
    try:
        with open(filePath) as textFile:
            ret = textFile.readlines()
    except:
        pass
    if len(ret) == 0:
        if logger:
            logger.warn("Couldn't load the initial "
                        "peer list. Try adding a "
                        "file named 'initial_peers.txt' "
                        "to {}".format(os.getcwd()))
    # Remove lines that start with a hash or are empty.
    return [x.strip() for x in ret if x != "" and not x.find("#") != -1]


def announceToPeers(filePath, host, logger=None):
    for peer in getInitialPeerList(filePath):
        try:
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            data = {"peer": {"url": peer},
                    "sender": {"url": host}}
            url = "{}/federation/announce".format(peer.rstrip("/"))
            requests.post(url, data=json.dumps(data), headers=headers)

        except Exception as e:
            if logger:
                logger.info("Couldn't announce to initial peer {}".format(
                    (e, url)))
