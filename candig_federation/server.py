#!/usr/bin/env python3

"""
Driver program for service
"""

import connexion
# from prometheus_flask_exporter import PrometheusMetrics
from flask_cors import CORS
import os.path
import os
import candigv2_logging.logging

candigv2_logging.logging.initialize()


def main():
    """
    Main Routine

    Set up server and service dictionaries
    """

    CONFIG_DIR = os.getenv("CONFIG_DIR", "../config")

    return APP

def configure_app():
    """
    Set up base flask app from Connexion

    App pulled out as global variable to allow import into
    testing files to access application context
    """
    app = connexion.FlaskApp(__name__, options={"swagger_url": "/"})
    app.add_api('federation.yaml', strict_validation=True, validate_responses=True)
    return app


APP = configure_app()
APPLICATION = main()

# expose flask app for uwsgi

application = APPLICATION.app
# metrics = PrometheusMetrics(application)
CORS(application)

if __name__ == '__main__':
    APPLICATION.run()
