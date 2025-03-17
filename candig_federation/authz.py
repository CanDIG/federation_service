from flask import Flask
import authx.auth
import os
from candigv2_logging.logging import CanDIGLogger
import server

SERVICE_TOKEN = server.SERVICE_TOKEN

logger = CanDIGLogger(__file__)


app = Flask(__name__)
TEST_KEY = os.getenv("TEST_KEY", None)

def is_testing(request):
    if request.headers.get("Test_Key") == TEST_KEY:
        logger.warning("TEST MODE, AUTHORIZATION IS DISABLED")
        return True


def is_site_admin(request):
    """
    Is the user associated with the token a site admin?
    """
    if request.headers.get("Test_Key") == TEST_KEY:
        logger.warning("TEST MODE, AUTHORIZATION IS DISABLED")
        return True # no auth
    if "Authorization" in request.headers:
        try:
            return authx.auth.is_site_admin(request)
        except Exception as e:
            logger.error(f"Couldn't authorize site_admin: {type(e)} {str(e)}")
            return False
    return False
