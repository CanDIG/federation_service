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
from flask_session import Session
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
    parser.add_argument('--services', default="./configs/services1.txt")
    args = parser.parse_args(args)


    # Logging configuration

    # app = connexion.FlaskApp(__name__, server='tornado')
    #
    # api_def = pkg_resources.resource_filename('candig_federation', 'api/federation.yaml')
    #
    # app.add_api(api_def, strict_validation=True, validate_responses=True)

    log_handler = logging.FileHandler(args.logfile)
    numeric_loglevel = getattr(logging, args.loglevel.upper())
    log_handler.setLevel(numeric_loglevel)

    app.app.logger.addHandler(log_handler)
    app.app.logger.setLevel(numeric_loglevel)

    # Peer Setup
    app.app.config["peers"] = network.parseConfigList("./configs/peerlist.txt")
    app.app.config["self"] = "http://{}:{}".format(args.host, args.port)

    # Service Parse
    app.app.config["services"] = network.parseConfigList(args.services)

    #app.run(port=args.port)

    return app, args.port

def configure_app():
    app = connexion.FlaskApp(__name__, server='tornado')

    api_def = pkg_resources.resource_filename('candig_federation', 'api/federation.yaml')

    app.add_api(api_def, strict_validation=True, validate_responses=True)

    return app

app = configure_app()

application, port = main()


if __name__ == '__main__':
    application.run(port=port)
