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


def main(args=None):
    """Main Routine"""
    if args is None:
        args = sys.argv[1:]

    print(args)

    parser = argparse.ArgumentParser('Run federation service')
    parser.add_argument('--port', default=8890)
    parser.add_argument('--host', default='10.9.208.132')
    parser.add_argument('--logfile', default="./log/federation.log")
    parser.add_argument('--loglevel', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
    parser.add_argument('--services', default="./configs/services3.json")
    parser.add_argument('--peers', default="./configs/peers.json")
    parser.add_argument('--schemas', default="./configs/schemas.json")
    args, unknown = parser.parse_known_args()

    # Logging configuration

    log_handler = logging.FileHandler(args.logfile)
    numeric_loglevel = getattr(logging, args.loglevel.upper())
    log_handler.setLevel(numeric_loglevel)

    app.app.logger.addHandler(log_handler)
    app.app.logger.setLevel(numeric_loglevel)

    # Peer Setup

    app.app.config["peers"] = network.parseConfigs("peers", args.peers, args.schemas, app.app.logger)
    app.app.config["self"] = "http://{}:{}".format(args.host, args.port)

    # Service Parse
    app.app.config["services"] = network.parseConfigs("services", args.services, args.schemas, app.app.logger)

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
