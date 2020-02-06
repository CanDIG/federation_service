"""

Provides methods to handle both local and federated requests
"""

import json
import requests
from flask import current_app
from requests_futures.sessions import FuturesSession

APP = current_app


class FederationResponse:
    """
    This is a collection of methods to facilitate federated queries across the CanDIG network

    :param request: The type of HTTP request to federate, either GET or POST. PUT TBD
    :type request: str
    :param url: URL of the CanDIG service to be queried
    :type url: str
    :param endpoint_path: Specific API endpoint of CanDIG service to be queried, may contain query string if GET
    :type endpoint_path: str
    :param endpoint_payload: Query string or data needed by endpoint specified in endpoint_path
    :type endpoint_payload: object, {param0=value0, paramN=valueN} for GET, JSON struct dependent on service endpoint for POST
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments

    def __init__(self, request, url, endpoint_path, endpoint_payload, request_dict, service, return_mimetype='application/json',
                 timeout=5):
        self.results = []
        self.status = []
        self.request = request
        self.url = url
        self.endpoint_path = endpoint_path
        self.endpoint_payload = endpoint_payload
        self.service = service
        self.return_mimetype = return_mimetype
        self.request_dict = request_dict
        self.token = self.request_dict.headers['Authorization']
        self.logger = APP.logger
        self.header = {
            'Content-Type': self.return_mimetype,
            'Accept': self.return_mimetype,
            'Federation': 'false',
            'Authorization': self.token,
        }
        self.service_headers = {}
        self.timeout = timeout

    def announce_fed_out(self, request_type, destination, path, args):
        self.logger.info(json.dumps({"Sending": "{} -> {}/{}. Args: {}".format(
            request_type, destination, path, args
        )}))

    def announce_fed_in(self, source, code, response):
        self.logger.info(json.dumps({"Received": "{} From {}. Data: {}".format(
            code, source, response
        )}))

    def get_service(self, url, endpoint_path, endpoint_payload):
        """
        make local data request and set the results and status for a FederationResponse
        """
        try:
            request_handle = requests.Session()
            full_path = "{}/{}".format(url, endpoint_path)
            # self.announce_fed_out("GET", url, endpoint_path, endpoint_payload)
            resp = request_handle.get(full_path, headers=self.header, params=endpoint_payload, timeout=self.timeout)
            self.status.append(resp.status_code)


            if isinstance(resp.json(), list):
                self.results.extend(resp.json())
                # self.announce_fed_in(full_path, resp.status_code, resp.json())
            else:
                # Only take the 'data' portion of the Response

                response = [{key: value for key, value in resp.json().items() if key.lower()
                             not in ['headers', 'url']}]
                # self.announce_fed_in(full_path, resp.status_code, response)
                self.results.extend(response)

        except requests.exceptions.ConnectionError:
            self.status.append(404)
            return
        except requests.exceptions.Timeout:
            self.status.append(504)
            return

    def federate_check(self):
        if 'Federation' in self.request_dict.headers and \
                self.request_dict.headers.get('Federation').lower() == 'false':
            return False
        else:
            return True

    def post_service(self, url, endpoint_path, endpoint_payload):
        """
        make local data request and set the results and status for a FederationResponse
        """
        try:
            request_handle = requests.Session()
            full_path = "{}/{}".format(url, endpoint_path)
            # self.announce_fed_out("POST", url, endpoint_path, endpoint_payload)
            resp = request_handle.post(full_path, headers=self.header, json=endpoint_payload)
            self.status.append(resp.status_code)

            if isinstance(resp.json(), list):
                self.results.extend(resp.json())
                # self.announce_fed_in(full_path, resp.status_code, resp.json())

            else:
                # Only take the 'data' portion of the Response
                response = [{key: value for key, value in resp.json().items() if key.lower()
                             not in ['headers', 'url', 'args', 'json']}]
                # self.announce_fed_in(full_path, resp.status_code, resp.json())
                self.results.extend(response)

        except requests.exceptions.ConnectionError:
            self.status.append(404)
            return

        except requests.exceptions.Timeout:
            self.status.append(504)
            return

    def handle_peer_request(self, request, endpoint_path, endpoint_payload, header):
        """

        Make peer data requests and update the results and status for a FederationResponse

        If a response from a peer is recieved, it will be a Response Object with keypairs
            {"status": [], "results":[] }

        The data structures within results are still unknown/undefined at this time, so
        just append everything instead of attempting to aggregate internal structs.
        """

        uri_list = []

        for peer in APP.config["peers"].values():
            uri_list.append("{}".format(peer))

        for future_response in self.async_requests(uri_list=uri_list,
                                                   request_type=request,
                                                   header=header,
                                                   endpoint_payload=endpoint_payload,
                                                   endpoint_path=endpoint_path):
            try:
                response = future_response.result()
            except AttributeError:
                if isinstance(future_response, requests.exceptions.ConnectionError):
                    self.status.append(404)
                if isinstance(future_response, requests.exceptions.Timeout):
                    self.status.append(504)
                continue
            except requests.exceptions.ConnectionError:
                self.status.append(404)
                continue
            except requests.exceptions.Timeout:
                self.status.append(504)
                continue

            # If the call was successful append the results

            if response.status_code in [200, 201, 405]:
                try:
                    """
                    Each Response will be in the form on a ResponseObject
                        {"status": [], "results": []}
                    Gather the data within each "results" and append it to
                    the main one.
                    """

                    self.results.extend(response.json()["results"])
                    self.status.append(response.status_code)

                except KeyError:
                    # No "results"
                    self.logger.warn(KeyError)
                    self.status.append(500)
                    self.results.append(
                        {"Error": "Malformed Response Object: No 'results'"})
                    pass

                except ValueError:
                    # JSON decoding failure
                    self.logger.warn(ValueError)
                    self.status.append(500)
                    self.results.append(
                        {"Error": "Malformed Response Object: No JSON data"})
                    pass

        # Return is used for testing individual methods
        return self.results

    def async_requests(self, uri_list, request_type, endpoint_path, endpoint_payload, header):
        """
        Use futures session type to async process peer requests
        :return: list of future responses
        """
        args = {"endpoint_path": endpoint_path, "endpoint_payload": endpoint_payload}
        async_session = FuturesSession(max_workers=10)  # capping max threads
        responses = []

        if request_type == "GET":
            for uri in uri_list:

                try:
                    # self.announce_fed_out(request_type, uri, endpoint_path, endpoint_payload)
                    responses.append(async_session.get(uri,
                                                       headers=header, params=args, timeout=self.timeout))
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    responses.append(e)
        elif request_type == "POST":
            for uri in uri_list:
                try:
                    # self.announce_fed_out(request_type, uri, endpoint_path, endpoint_payload)
                    responses.append(async_session.post(uri,
                                                        json=args, headers=header, timeout=self.timeout))
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    responses.append(e)

        return responses

    def merge_status(self, statuses):
        """
        Design discussion has converged towards returning a single status

        Priority List:
        1. Return 200 if one exists within the list
        2. 500 > 408 > 404
        """

        if len(statuses) == 1:
            return statuses[0]

        elif 200 in statuses:
            return 200

        elif 201 in statuses:
            return 201

        elif 405 in statuses:
            return 405

        elif 500 in statuses:
            return 500

        elif 504 in statuses:
            return 504

        elif 404 in statuses:
            return 404

        else:
            return 500

    def get_response_object(self):
        """
        1. Check if federation is needed
         1a. Broadcast if needed
        2. If no federation is required, passed endpoint to service
        3. Aggregate and return all the responses.

        :return: formatted dict that can be returned as application/json response
        """

        if self.request == "GET":

            if self.federate_check():
                self.handle_peer_request(request="GET",
                                         endpoint_path=self.endpoint_path,
                                         endpoint_payload=self.endpoint_payload,
                                         header=self.header)

            else:
                self.get_service(url=self.url,
                                 endpoint_path=self.endpoint_path,
                                 endpoint_payload=self.endpoint_payload)
        else:

            if self.federate_check():
                self.handle_peer_request(request="POST",
                                         endpoint_path=self.endpoint_path,
                                         endpoint_payload=self.endpoint_payload,
                                         header=self.header)
            else:
                self.post_service(url=self.url,
                                  endpoint_path=self.endpoint_path,
                                  endpoint_payload=self.endpoint_payload)

        status = self.merge_status(self.status)
        try:
            # Remove duplicates from a list response due to Federated querying
            response = {"status": status, "results": sorted(list(set(self.results))), "service": self.service}

        except TypeError:
            # Dealing with dicts objects
            response = {"status": status, "results": self.results, "service": self.service}
        
        return response, status, self.service_headers

