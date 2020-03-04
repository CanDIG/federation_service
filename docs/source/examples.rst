Sending a Request
=================

There are a number of ways to send requests to the Federation service, ranging from 
simple cURL commands, to programs such as Insomnia or Postman. Throughout development,
the simplest and most modular method was to just create a wrapper function around the
Requests package and invoke that whenever a path needed to be queried.

.. code-block:: python

    import json
    import requests

    # Wrapper function that directly communicates with Federation

    def send_post_request(type, path, payload=None, dest=1):
        url = {1: "http://federationaddress.com/federation/search",
            2: "http://federationaddress2.com/federation/search"}

        jsondata = {"request_type": type,"endpoint_path": path, "endpoint_payload": payload}
        request_handle = requests.Session()
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "federation": 'false',
            "Authorization": "Bearer " + "iZTFhLTRiZDItODdk"
        }

        return request_handle.post(url[dest], headers=headers, json=jsondata)


    # Wrapper function that includes Tyk authentication/gateway services

    def send_post_request(type, path, payload=None, dest=1):
        url = {1: "http://tykgatewayaddress.com/federation",
            2: "http://tykgatewayaddress.com/federation2"}

        jsondata = {"request_type": type,"endpoint_path": path, "endpoint_payload": payload}
        request_handle = requests.Session()
        creds = {"username": "CanDIG", "password": "IsGreat"}
        token = request_handle.post("http://tykgatewayaddress.com/auth/token", json=creds)
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "federation": 'false',
            "Authorization": "Bearer " + token.json()['id_token']
        }

        return request_handle.post(url[dest], headers=headers, json=jsondata)


With this function, it's simple to query any downstream service:

.. code-block:: python

    payload = {
    "id": "247e28c3-7940-4420-8a4f-fb3c152d4cc2",
    "version": "0.4",
    "tags": ["magenta"],
    "name": "Example",
    "description": "string",
    "created": "string",
    "ontologies": [
            {
                "id": "duo",
                "terms": [{"id": "DUO:0000026"}, {"id": "DUO:0000011"}, {"id": "DUO:0000027"}]
            }
        ]
    }

    send_post_request("POST", "datasets", payload)

    send_post_request("GET", "datasets/search/ontologies")

    send_post_request("GET", "datasets/search?ontologies=DUO:0000027")

    send_post_request("GET", "datasets/247e28c3794044208a4ffb3c152d4cc2")

    send_post_request("GET", "datasets/search", {"tags": "gold", "ontologies": ["DUO:0000001", "DUO:0000011"]})



Why No GET?
===========

A question that may come to mind when looking at these examples is why specify GET or POST within a POST request_handle
rather than just sending a GET request directly to be passed on? This was the case at first, but it quickly became convoluted
to pass complex search queries as strings formatted as dictionaries or json objects. Utilizing the POST body to pass on all the
endpoint arguments to a GET request makes it much easier from both a user and coding standpoint.

