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

### How to register services

Specify the name and URL of your services.Below is an example of `services.json`:

```
{
  "services": {
    "katsu": "https://katsu-api-2.herokuapp.com",
    "candig-server": "https://app05.herokuapp.com"
  }
}
```

### How to register peer servers

For federation to work, you will need to register both the `host` and its peer servers as `servers` under `config/servers.json`. This may be confusing, as you may think that your `host` does not need to be registered.

In addition, specify the location for your peer servers with the array `["research centre", "province name", "province code"]`. For compatibility with CanDIG's [data portal](https://github.com/CanDIG/candig-data-portal), use the following province codes:

`'ca-ab', 'ca-bc', 'ca-mb', 'ca-nb', 'ca-nl', 'ca-nt', 'ca-ns', 'ca-nu', 'ca-on', 'ca-pe', 'ca-qc', 'ca-sk', 'ca-yt'`


For example, if your host federation service is running at `http://0.0.0.0:8890` in British Columbia, and your first 
peer server federation service is running at `http://0.0.0.0:8891` in Ontario, your `servers.json` would look like this:

```
{
  "servers": [
    {
      "url": "http://ga4ghdev01.bcgsc.ca:8891/federation/search",
      "location": [
        "BCGSC",
        "British Columbia",
        "ca-bc"
      ]
    },
    {
      "url": "http://ga4ghdev01.bcgsc.ca:8892/federation/search",
      "location": [
        "UHN",
        "Ontario",
        "ca-on"
      ]
    }
  ]
}
```

## Running

You should use `uwsgi` to run the app for all functionalities to work as expected. The `--master` flag enables graceful reloading of the server without closing the socket and is useful to apply  any changes to the code while developing. For more details, read the [uwsgi documentation](https://uwsgi-docs.readthedocs.io/en/latest/Management.html).

```
# Run Server
uwsgi federation.ini --http :8891 --master

# Reload server gracefully, replace <pid> with the uwsgi process ID
kill -HUP <pid>
```

You may also start the server with the following command, but federation queries will not work. The command below is usually for debugging purposes.

```
python -m candig_federation --host 0.0.0.0 --port 8080 --services ./configs/services.json --servers configs/servers.json
```

Once the service is running, a Swagger UI can be accessed at : `/federation/ui`


### Testing

Tests can be run with pytest and coverage:

```
pytest --cov=candig_federation tests/
```

To generate a readable html report of the test results, use:

```
pytest tests/ --cov=candig_federation --html=test_report.html --self-contained-html
```


## Documentation

There is a [documentation website](https://federation-service.readthedocs.io/en/latest) with detailed information on how federated queries work and how they are tested.
