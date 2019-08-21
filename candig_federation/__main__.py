#!/usr/bin/env python3

"""
Driver program for service
"""

import sys
import argparse
import logging

import connexion
import pkg_resources

from candig_federation.api import network


def main(args=None):
    """
    Main Routine

    Parse all the args and set up peer and service dictionaries
    """
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser('Run federation service')
    parser.add_argument('--port', default=8890)
    parser.add_argument('--host', default='10.9.208.132')
    parser.add_argument('--logfile', default="./log/federation.log")
    parser.add_argument('--loglevel', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
    parser.add_argument('--services', default="./configs/services3.json")
    parser.add_argument('--peers', default="./configs/peers.json")
    parser.add_argument('--schemas', default="./configs/schemas.json")

    # known args used to supply command line args to pytest without raising an error here
    args, _ = parser.parse_known_args()

    # Logging configuration

    log_handler = logging.FileHandler(args.logfile)
    numeric_loglevel = getattr(logging, args.loglevel.upper())
    log_handler.setLevel(numeric_loglevel)

    APP.app.logger.addHandler(log_handler)
    APP.app.logger.setLevel(numeric_loglevel)

    # Peer Setup

    APP.app.config["peers"] = network.parse_configs("peers", args.peers,
                                                    args.schemas, APP.app.logger)
    APP.app.config["self"] = "http://{}:{}".format(args.host, args.port)

    # Service Parse
    APP.app.config["services"] = network.parse_configs("services", args.services,
                                                       args.schemas, APP.app.logger)

    return APP, args.port


def configure_app():
    """
    Set up base flask app from Connexion

    App pulled out as global variable to allow import into
    testing files to access application context
    """
    app = connexion.FlaskApp(__name__, server='tornado')

    api_def = pkg_resources.resource_filename('candig_federation', 'api/federation.yaml')

    app.add_api(api_def, strict_validation=True, validate_responses=True)

    return app


APP = configure_app()

APPLICATION, PORT = main()


if __name__ == '__main__':
    print("federation_service running at {}".format(APPLICATION.app.config["self"]))
    APPLICATION.run(port=PORT)
