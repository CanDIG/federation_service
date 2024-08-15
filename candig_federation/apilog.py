
"""
Logging wrappers for api calls
"""

import json
from datetime import datetime
from uuid import UUID
from decorator import decorator
from connexion import request
from candigv2_logging.logging import CanDIGLogger


logger = CanDIGLogger(__file__)


class FieldEncoder(json.JSONEncoder):
    """Wrap fields to be JSON-safe; handle datetime & UUID"""
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


@decorator
def apilog(func, *args, **kwargs):
    """
    Logging decorator for API calls
    """
    entrydict = {}
    try:
        entrydict['address'] = request.remote_addr
        entrydict['data'] = request.json
    except RuntimeError:
        entrydict['called'] = func.__name__
        entrydict['args'] = args
        for key in kwargs:
            entrydict[key] = kwargs[key]

    try:
        logger.log_message("INFO", entrydict, request=request)
    except Exception as e:
        logger.log_message("DEBUG", str(e))
    return func(*args, **kwargs)
