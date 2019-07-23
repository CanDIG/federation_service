"""

Provides methods to handle both local and federated requests
"""

import requests
import json

import candig_federation.api.network as network
from flask import current_app
from requests_futures.sessions import FuturesSession

from collections import Counter

app = current_app

class FederationResponse(object):

    def __init__(self, request, path, url, host, return_mimetype, request_dict):
        self.results = {}
        self.status = []
        self.request = request
        self.path = path
        self.url = url
        self.host = host
        self.return_mimetype = return_mimetype
        self.request_dict = request_dict
        self.token = "blank"

    def handleLocalRequest(self):
        """

        make local data request and set the results and status for a FederationResponse
        """
        try:

            if self.request == "GET":
                headers = {'Content-Type': 'application/json',
                           'Accept': 'application/json'}

                print(self.host, self.path)

                request_handle = requests.Session()

                full_path = "{}/{}".format(self.url, self.path)

                resp = request_handle.get(full_path, headers=headers)

                self.status.append(resp.status_code)

                response = {key: value for key, value in resp.json().items() if key.lower() not in ['headers', 'url']}

                self.results = response

        except requests.exceptions.ConnectionError:
            self.status.append(404)


    def handlePeerRequest(self, request_type):
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
        for peer in app.config["peers"]:
            if peer != app.config["self"]:
                uri_list.append(peer)

        for future_response in self.async_requests(uri_list, request_type, header):
            try:
                response = future_response.result()
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                self.status.append(503)
                continue
            self.status.append(response.status_code)
            # If the call was successful append the results
            if response.status_code == 200:
                try:
                    if request_type == "GET":
                        self.results = response.json()['results']

                    elif request_type == "POST":
                        peer_response = response.json()['results']

                        if not self.results:
                            self.results = peer_response
                        else:
                            for key in peer_response:
                                if key in ['nextPageToken', 'total']:
                                    if key not in self.results:
                                        self.results[key] = peer_response[key]
                                    continue
                                for record in peer_response[key]:
                                    self.results[key].append(record)
                except ValueError:
                    pass

        if self.results:
            self.mergeCounts()

    def mergeCounts(self):
        """

        merge federated counts and set results for FederationResponse
        """

        table = list(set(self.results.keys()))
        prepare_counts = {}
        print(self.results)
        print("\n\n\n\n")
        for record in self.results[table]:
            for k, v in record.items():
                if k in prepare_counts:
                    prepare_counts[k].append(Counter(v))
                else:
                    prepare_counts[k] = [Counter(v)]

        merged_counts = {}
        for field in prepare_counts:
            count_total = Counter()
            for count in prepare_counts[field]:
                count_total = count_total + count
            merged_counts[field] = dict(count_total)
        print(table, merged_counts)
        self.results[table] = [merged_counts]


    def async_requests(self, uri_list, request_type, header):
        """
        Use futures session type to async process peer requests
        :return: list of future responses
        """

        async_session = FuturesSession(max_workers=10) # capping max threads
        if request_type == "GET":
            responses = [
                async_session.get(uri, headers=header)
                for uri in uri_list
            ]
        elif request_type == "POST":
            responses = [
                async_session.post(uri, json=json.loads(self.request), headers=header)
                for uri in uri_list
            ]
        else:
            responses = []
        return responses

    def getResponseObject(self):
        """
        :return: formatted dict that can be returned as application/json response
        """
        return {'status':self.status, 'results':self.results}