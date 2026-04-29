# from prometheus_flask_exporter import PrometheusMetrics
from flask_cors import CORS
import connexion
import candigv2_logging.logging
import authx.auth
import os

candigv2_logging.logging.initialize()
logger = candigv2_logging.logging.CanDIGLogger(__file__)

# Create the application instance
app = connexion.FlaskApp(__name__, specification_dir='./')
CORS(app.app)

app.add_api('federation.yaml', strict_validation=True, validate_responses=True)

TEST_KEY = os.getenv("TEST_KEY", None)
SERVICE_TOKEN = None
if TEST_KEY is not None and SERVICE_TOKEN is None:
    logger.debug("creating service token")
    try:
        with open("/home/candig/service_token.txt") as f:
            SERVICE_TOKEN = f.read().strip()
    except FileNotFoundError:
        logger.debug("no token found")
        pass
else:
    SERVICE_TOKEN = TEST_KEY

@app.route('/')
def index():
    return 'INDEX'


if __name__ == '__main__':
    app.run()
