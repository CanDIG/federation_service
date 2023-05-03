from flask import Flask
import authx.auth
import os


app = Flask(__name__)
TEST_KEY = os.getenv("TEST_KEY")
CANDIG_OPA_URL = os.getenv("CANDIG_OPA_URL")
CANDIG_OPA_SECRET = os.getenv("CANDIG_OPA_SECRET")
TYK_FEDERATION_API_ID = os.getenv("TYK_FEDERATION_API_ID")


def is_testing(request):
    if request.headers.get("Test_Key") == TEST_KEY:
        print("WARNING: TEST MODE, AUTHORIZATION IS DISABLED")
        app.logger.warning("WARNING: TEST MODE, AUTHORIZATION IS DISABLED")
        return True


def is_site_admin(request):
    """
    Is the user associated with the token a site admin?
    """
    if request.headers.get("Test_Key") == TEST_KEY:
        print("WARNING: TEST MODE, AUTHORIZATION IS DISABLED")
        app.logger.warning("WARNING: TEST MODE, AUTHORIZATION IS DISABLED")
        return True # no auth
    if "Authorization" in request.headers:
        try:
            return authx.auth.is_site_admin(request, opa_url=CANDIG_OPA_URL, admin_secret=CANDIG_OPA_SECRET)
        except Exception as e:
            print(f"Couldn't authorize site_admin: {type(e)} {str(e)}")
            app.logger.warning(f"Couldn't authorize site_admin: {type(e)} {str(e)}")
            return False
    return False


def add_provider_to_tyk(token, issuer):
    return authx.auth.add_provider_to_tyk_api(TYK_FEDERATION_API_ID, token, issuer)


def remove_provider_to_tyk(issuer):
    return authx.auth.remove_provider_to_tyk_api(TYK_FEDERATION_API_ID, issuer)


def add_provider_to_opa(token, issuer):
    return authx.auth.add_provider_to_opa(token, issuer)


def remove_provider_to_opa(issuer):
    return authx.auth.remove_provider_to_opa(issuer)