#!/usr/bin/env python3

"""
Driver program for service
"""

import sys
import connexion
import argparse
import logging
import pkg_resources

from candig_federation.api import network
from tornado.options import define

def main(args=None):
    """Main Routine"""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser('Run federation service')
    parser.add_argument('--port', default=8889)
    parser.add_argument('--host', default='10.9.208.132')
    parser.add_argument('--logfile', default="./log/federation.log")
    parser.add_argument('--loglevel', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
    args = parser.parse_args(args)


    # Application setup

    app = connexion.FlaskApp(__name__, server='tornado')


    # Logging configuration

    log_handler = logging.FileHandler(args.logfile)
    numeric_loglevel = getattr(logging, args.loglevel.upper())
    log_handler.setLevel(numeric_loglevel)

    app.app.logger.addHandler(log_handler)
    app.app.logger.setLevel(numeric_loglevel)

    # Peer Setup
    app.app.config["peers"] = network.getInitialPeerList("./configs/peerlist.txt")
    app.app.config["self"] = "http://{}:{}".format(args.host, args.port)

    #network.announceToPeers("./configs/peerlist.txt", sender, app.app.logger)



    # Add in swagger API

    api_def = pkg_resources.resource_filename('candig_federation', 'api/federation.yaml')

    app.add_api(api_def, strict_validation=True, validate_responses=True)

    app.run(port=args.port)


if __name__ == '__main__':
    main()
