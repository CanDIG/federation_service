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

## Configuration Files

The Federation Service requires two JSON configuration files to be placed into the `federation_service/configs` directory. 
These files are `servers.json` and `services.json`.

#### How to register services

Below is an example of `services.json`

```
{
  "services": {
    "katsu": "https://katsu-api-2.herokuapp.com",
    "candig-server": "https://app05.herokuapp.com"
  }
}
```

#### How to register peer servers

For federation to work, you will need to register both the `host` and its peer servers as `servers` under `config/servers.json`.

This may be confusing, as you may think that your `host` does not need to be registered.

For example, if your host federation service is running at `http://0.0.0.0:8890`, and your first 
peer server federation service is running at `http://0.0.0.0:8891`, your `servers.json` would look like this:

```
{
  "servers": {
    "p1": "http://ga4ghdev01.bcgsc.ca:8890/federation/search",
    "p2": "http://ga4ghdev01.bcgsc.ca:8891/federation/search"
  }
}
```

### Running

You should use `uwsgi` to run the app with the following command for all functionalities to work as expected.

```
uwsgi federation.ini --http 0.0.0.0:8080
```

You may also start the server with the following command, but federation queries will not work. The command below is for usually for debugging purposes.

```
python -m candig_federation --host 0.0.0.0 --port 8080 --services ./configs/services.json --servers configs/servers.json
```

Once the service is running, a Swagger UI can be accessed at : `/federation/ui`


### Testing

Tests can be run with pytest and coverage:

```pytest --cov=candig_federation tests/```

To generate a readable html report of the test results, use:
```pytest --cov=candig_federation tests/ --html=test_report.html --self-contained-html```


## Documentation

There is a documentation website available [here](https://candig-federation.readthedocs.io/en/latest/index.html) with detailed information on how federation works and how it's tested.