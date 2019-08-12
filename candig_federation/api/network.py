"""
Provides methods to initialize the server's peer to peer connections.
"""

import os
import requests
import json
import jsonschema


def parseConfigList(filePath, logger=None):
    """
    Attempts to get a list of peers/services from a file specified in configuration.
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
    apiToURI = [x.strip() for x in ret if x != "" and not x.find("#") != -1]

    print(apiToURI[0].split(":"))

    apiDict = {line.split(":")[0]: line.split(":")[1] for line in apiToURI}

    return apiDict




def parsePeerList(schema, filePath, logger=None):
    """
    Attempts to get a list of peers from a json file specified in configuration.
    This file should have a json structure matching the schema specified.

    """
    SCHEMA_DICT = getSchemaDict("{}/configs/schemas.json".format(os.getcwd()))

    if schema not in SCHEMA_DICT.keys():
        if logger:
            logger.warn("{} not in known schemas."
                        "Please check spelling or"
                        "add the schema ")

    try:
        with open(filePath) as json_file:
            data = json.load(json_file)
            print(data)
            jsonschema.validate(data, schema=SCHEMA_DICT[schema])
            return data[schema]
    except FileNotFoundError:
        if logger:
            logger.warn("Couldn't load the initial "
                        "peer list. Try adding a "
                        "file named 'peers.json' "
                        "to {}/configs".format(os.getcwd()))
        else:
            raise FileNotFoundError
    except jsonschema.ValidationError as VE:
        if logger:
            logger.warn("Peers object in peers.json "
                        "did not validate against the"
                        "schema. Please recheck file.")
            logger.warn(VE)
        else:
            raise jsonschema.ValidationError



def getSchemaDict(filePath, logger=None):
    try:
        with open(filePath) as json_file:
            return json.load(json_file)
    except FileNotFoundError as FNE:
        if logger:
            logger.warn("Unable to find schema file."
                        "Please check spelling or place"
                        "a 'schemas.json' at"
                        "{}/configs".format(os.getcwd()))
        else:
            raise FileNotFoundError
