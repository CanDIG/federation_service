# federation_service
Microservice implementation of Federation Service for CanDIG v2

Based on CanDIG demo projects: [OpenAPI variant service demo](https://github.com/ljdursi/openapi_calls_example), [Python Model Service](https://github.com/CanDIG/python_model_service).


## Stack

- [Connexion](https://github.com/zalando/connexion) for implementing the API
- [Bravado-core](https://github.com/Yelp/bravado-core) for Python classes from the spec
- Python 3
- Pytest

## Installation

The federation_service can be installed in a py3.7+ virtual environment:

```
pip install -r requirements.txt
```

### How to register peer servers

On initialization of the docker container, the server listed in .env as FEDERATION_SELF_SERVER will be registered. This is your own server. If you want to register other peer servers, use the /federation/v1/servers POST endpoint, described in federation.yaml. This call must be authorized with a bearer token from a site administrator for your own server. In the `authentication` object, you'll need to have a valid JWT from the peer server's identity issuer, as well as the URL of the issuer.

```
## add server
curl -X "POST" "http://candig.docker.internal:5080/federation/v1/servers" \
     -H 'Content-Type: application/json' \
     -H 'Authorization: Bearer <site admin token>' \
     -d $'{
      "server": {
        "id": "new-candig",
        "url": "http://some-place.candig.ca",
        "location": {
          "name": "New CanDIG",
          "province": "ON",
          "province-code": "ca-on"
        }
      },
      "authentication": {
        "issuer": "https://some-place.candig.ca/auth/realms/candig",
        "token": "<token from issuer>"
      }
    }'
```

## Running

You should use `uwsgi` to run the app for all functionalities to work as expected. The `--master` flag enables graceful reloading of the server without closing the socket and is useful to apply  any changes to the code while developing. For more details, read the [uwsgi documentation](https://uwsgi-docs.readthedocs.io/en/latest/Management.html).

```
# Run Server
uwsgi federation.ini --master

# Reload server gracefully, replace <pid> with the uwsgi process ID
kill -HUP <pid>
```

Once the service is running, a Swagger UI can be accessed at : `/federation/v1`.


### Testing

Tests can be run with pytest:

```
pytest tests/test_uniform_federation.py
```

However, the tests are best run inside the docker container, if you're running in the CanDIGv2 environment:
```
docker exec candigv2_federation_1 pytest
```


## Documentation

There is a [documentation website](https://federation-service.readthedocs.io/en/latest) with detailed information on how federated queries work and how they are tested.
