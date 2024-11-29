# from prometheus_flask_exporter import PrometheusMetrics
from flask_cors import CORS
import connexion
import candigv2_logging.logging

candigv2_logging.logging.initialize()

# Create the application instance
app = connexion.FlaskApp(__name__, specification_dir='./')
CORS(app.app)

app.add_api('federation.yaml', strict_validation=True, validate_responses=True)

def main():
    # Create the application instance
    app = connexion.FlaskApp(__name__, specification_dir='./')
    CORS(app.app)

    app.add_api('federation.yaml', strict_validation=True, validate_responses=True)
    return app

if __name__ == '__main__':
    app.run()
