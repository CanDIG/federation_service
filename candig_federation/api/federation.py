"""

Provides methods to handle both local and federated requests
"""

from collections import Counter

import requests
from requests.exceptions import Timeout
import urllib3
from socket import timeout
from flask import current_app
from requests_futures.sessions import FuturesSession

APP = current_app


class FederationResponse:
    """
    Class based methods utilized to store requests within instance variables
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments

    def __init__(self, request, url, endpoint_path, endpoint_payload, request_dict, return_mimetype='application/json', timeout=5):
        self.results = []
        self.status = []
        self.request = request
        self.url = url
        self.endpoint_path = endpoint_path
        self.endpoint_payload = endpoint_payload
        self.return_mimetype = return_mimetype
        self.request_dict = request_dict
        self.token = self.request_dict.headers['Authorization']

        self.header = {
            'Content-Type': self.return_mimetype,
            'Accept': self.return_mimetype,
            'Federation': 'false',
            'Authorization': self.token,
        }

        self.timeout = timeout

    def get_service(self, url, endpoint_path, endpoint_payload):
        """

        make local data request and set the results and status for a FederationResponse
        """
        try:
            request_handle = requests.Session()
            print("WHat the hell is going on\n")
            print(endpoint_path)
            full_path = "{}/{}".format(url, endpoint_path)

            print("Sending GET to: {}".format(full_path))
            resp = request_handle.get(full_path, headers=self.header, params=endpoint_payload, timeout=self.timeout)
            print(resp.json())
            self.status.append(resp.status_code)
            if resp.status_code == 200:
                response = {key: value for key, value in resp.json().items() if key.lower()
                            not in ['headers', 'url']}
                self.results.append(response)

        except requests.exceptions.ConnectionError:
            self.status.append(404)
            return
        except (urllib3.exceptions.ReadTimeoutError, timeout, Timeout):
            self.status.append(408)
            return 

    def federate_check(self):
        if 'Federation' not in self.request_dict.headers or \
                self.request_dict.headers.get('Federation') == 'true':
            return True

    def post_service(self, url, endpoint_path, endpoint_payload):
        """

        make local data request and set the results and status for a FederationResponse
        """
        try:
            request_handle = requests.Session()
            full_path = "{}/{}".format(url, endpoint_path)

            print("Sending POST to: {}".format(full_path))

            resp = request_handle.post(full_path, headers=self.header, json=endpoint_payload)
            self.status.append(resp.status_code)
            print(resp.json())
            if resp.status_code == 200:
                response = {key: value for key, value in resp.json().items() if key.lower()
                            not in ['headers', 'url', 'args', 'json']}
                self.results.append(response)

        except requests.exceptions.ConnectionError:
            self.status.append(404)

    def handle_peer_request(self, request, endpoint_path, endpoint_payload, header):
        """

        Make peer data requests and update the results and status for a FederationResponse

        If a response from a peer is recieved, it will be a Response Object with keypairs
            {"status": [], "results":[] }

        The data structures within results are still unknown/undefined at this time, so
        just append everything instead of attempting to aggregate internal structs.
        """

        # generate peer uri - This will still fail atm with Tyk as peers
        uri_list = []
        for peer in APP.config["peers"].values():
            if peer != APP.config["local"]:
                uri_list.append("{}".format(peer))

        print(uri_list)
        for future_response in self.async_requests(uri_list=uri_list,
                                                   request_type=request,
                                                   header=header,
                                                   endpoint_payload=endpoint_payload,
                                                   endpoint_path=endpoint_path):
            try:
                response = future_response.result()
                print(response.status_code)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                self.status.append(503)
                continue
            self.status.append(response.status_code)
            # If the call was successful append the results

            if response.status_code == 200:
                try:
                    if request == "GET":
                        self.results.append(response.json()["results"])

                    elif request == "POST":
                        peer_response = response.json()

                        if not self.results:
                            self.results = peer_response
                        else:

                            self.results.append(peer_response)
                except ValueError:
                    pass

        # Return is used for testing individual methods
        return self.results

        # if self.results:
        #     self.merge_counts()

    def merge_counts(self):
        """
        merge federated counts and set results for FederationResponse
        TODO: Fully Implement this
        """

        table = list(set(self.results.keys()))
        prepare_counts = {}

        for record in self.results:
            for key, value in record.items():
                if key in prepare_counts:
                    prepare_counts[key].append(Counter(value))
                else:
                    prepare_counts[key] = [Counter(value)]

        merged_counts = {}
        for field in prepare_counts:
            count_total = Counter()
            for count in prepare_counts[field]:
                count_total = count_total + count
            merged_counts[field] = dict(count_total)
        self.results[table] = [merged_counts]

    def async_requests(self, uri_list, request_type, endpoint_path, endpoint_payload, header):
        """
        Use futures session type to async process peer requests
        :return: list of future responses
        """
        args = {"endpoint_path": endpoint_path, "endpoint_payload": endpoint_payload}
        async_session = FuturesSession(max_workers=10)  # capping max threads
        if request_type == "GET":
            responses = [
                async_session.get("{}".format(uri),
                                  headers=header, params=args, timeout=self.timeout)
                for uri in uri_list
            ]

        elif request_type == "POST":
            responses = [
                async_session.post("{}".format(uri),
                                   json=args, headers=header)
                for uri in uri_list
            ]
        else:
            responses = []
        return responses

    def get_response_object(self):
        """
        1. Query service tied to the network (local)
        2. Check if the request needs to be federated and broadcast if so
        3. Aggregate and return all the responses.

        :return: formatted dict that can be returned as application/json response
        """

        if self.request == "GET":
            self.get_service(url=self.url,
                             endpoint_path=self.endpoint_path,
                             endpoint_payload=self.endpoint_payload)
            print("starting fed check")
            if self.federate_check():
                self.handle_peer_request(request="GET",
                                         endpoint_path=self.endpoint_path,
                                         endpoint_payload=self.endpoint_payload,
                                         header=self.header)
            print("done")
        else:
            self.post_service(url=self.url,
                              endpoint_path=self.endpoint_path,
                              endpoint_payload=self.endpoint_payload)
            if self.federate_check():
                self.handle_peer_request(request="POST",
                                         endpoint_path=self.endpoint_path,
                                         endpoint_payload=self.endpoint_payload,
                                         header=self.header)

        return {"status": self.status, "results": self.results}
