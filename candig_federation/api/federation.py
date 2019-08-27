"""

Provides methods to handle both local and federated requests
"""

from collections import Counter

import requests

from flask import current_app
from requests_futures.sessions import FuturesSession

APP = current_app


class FederationResponse:
    """
    Class based methods utilized to store requests within instance variables
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments

    def __init__(self, request_type, args, url, return_mimetype, request_dict):
        self.results = []
        self.status = []
        self.request = request_type
        self.args = args
        self.endpoint_path = args["endpoint_path"]
        self.endpoint_payload = args["endpoint_payload"]
        self.url = url
        self.return_mimetype = return_mimetype
        self.request_dict = request_dict
        self.token = "blank"

    def handle_local_request(self):
        """

        make local data request and set the results and status for a FederationResponse
        """
        try:
            request_handle = requests.Session()
            full_path = "{}/{}".format(self.url, self.endpoint_path)
            headers = {'Content-Type': 'application/json',
                       'Accept': 'application/json',
                       'Federation': 'false'}

            if self.request == "GET":
                resp = request_handle.get(full_path, headers=headers, params=self.endpoint_payload)
                self.status.append(resp.status_code)
                if resp.status_code == 200:
                    response = {key: value for key, value in resp.json().items() if key.lower()
                                not in ['headers', 'url']}
                    self.results.append(response)

            if self.request == "POST":
                resp = request_handle.post(full_path, headers=headers, json=self.endpoint_payload)
                self.status.append(resp.status_code)
                if resp.status_code == 200:
                    response = {key: value for key, value in resp.json().items() if key.lower()
                                not in ['headers', 'url', 'args', 'json']}
                    self.results.append(response)

        except requests.exceptions.ConnectionError:
            self.status.append(404)


    def handle_peer_request(self):
        """

        make peer data requests and update the results and status for a FederationResponse
        """

        header = {
            'Content-Type': self.return_mimetype,
            'Accept': self.return_mimetype,
            'Federation': 'False',
            'Authorization': self.token,
        }

        # generate peer uri
        uri_list = []
        for peer in APP.config["peers"].values():
            if peer != APP.config["self"]:
                uri_list.append(peer)

        for future_response in self.async_requests(uri_list, self.request, header):
            try:
                response = future_response.result()
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                self.status.append(503)
                continue
            self.status.append(response.status_code)
            # If the call was successful append the results

            if response.status_code == 200:
                try:
                    if self.request == "GET":
                        self.results.append(response.json()["results"])

                    elif self.request == "POST":
                        # peer_response = response.json()["results"]
                        peer_response = response.json()

                        if not self.results:
                            self.results = peer_response
                        else:
                            # for entries in peer_response["data"]["datasets"]:
                            #     print(self.results)
                            #     self.results["data"]["datasets"].append(entries)
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


    def async_requests(self, uri_list, request_type, header):
        """
        Use futures session type to async process peer requests
        :return: list of future responses
        """

        async_session = FuturesSession(max_workers=10)  # capping max threads
        if request_type == "GET":
            responses = [
                async_session.get("{}/federation/search".format(uri),
                                  headers=header, params=self.args)
                for uri in uri_list
            ]

        elif request_type == "POST":
            responses = [
                async_session.post("{}/federation/search".format(uri),
                                   json=self.args, headers=header)
                for uri in uri_list
            ]
        else:
            responses = []
        return responses

    def get_response_object(self):
        """
        :return: formatted dict that can be returned as application/json response
        """
        return {"status": self.status, "results": self.results}
