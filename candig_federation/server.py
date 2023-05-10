#!/usr/bin/env python3

"""
Driver program for service
"""

import connexion
# from prometheus_flask_exporter import PrometheusMetrics
from flask_cors import CORS
import os.path
import network
import logging


def main():
    """
    Main Routine

    Parse all the args and set up server and service dictionaries
    """

    # Logging configuration

    log_handler = logging.FileHandler("../config/federation.log")
    numeric_loglevel = getattr(logging, "INFO")
    log_handler.setLevel(numeric_loglevel)

    APP.app.logger.addHandler(log_handler)
    APP.app.logger.setLevel(numeric_loglevel)

    APP.app.config["service_file"] = os.path.abspath("../config/services.json")
    if not os.path.exists(APP.app.config["service_file"]):
        with open(APP.app.config["service_file"], "w") as f:
            f.write("{}")

    APP.app.config["server_file"] = os.path.abspath("../config/servers.json")
    if not os.path.exists(APP.app.config["server_file"]):
        with open(APP.app.config["server_file"], "w") as f:
            f.write("{}")

    return APP

def configure_app():
    """
    Set up base flask app from Connexion

    App pulled out as global variable to allow import into
    testing files to access application context
    """
    app = connexion.FlaskApp(__name__, options={"swagger_url": "/"})


    api_def = 'federation.yaml'

    app.add_api(api_def, strict_validation=True, validate_responses=True)
    return app


APP = configure_app()
APPLICATION = main()

# expose flask app for uwsgi

application = APPLICATION.app
# metrics = PrometheusMetrics(application)
CORS(application)


if __name__ == '__main__':
    APPLICATION.run()
