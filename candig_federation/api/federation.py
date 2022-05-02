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
    :param request_dict: Flask request object to be modified and forwarded along to service
    :type request_dict: Flask.Request
    :param service: Name of CanDIG service to be queried, used for log tracking
    :type service: str
    :param return_mimetype: HTTP content-type, default is application/json
    :type return_mimetype: str
    :param timeout: Wait time before a request times out, default is 5 seconds
    :type timeout: int
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments


    def __init__(self, request, url, endpoint_path, endpoint_payload, request_dict, endpoint_service, return_mimetype='application/json',
                 timeout=15):
        """Constructor method
        """
        self.result = {}
        self.results = {}
        self.status = []
        self.request = request
        self.url = url
        self.endpoint_path = endpoint_path
        self.endpoint_payload = endpoint_payload
        self.endpoint_service = endpoint_service
        self.return_mimetype = return_mimetype
        self.request_dict = request_dict
        self.logger = APP.logger
        
        try:
            self.token = self.request_dict.headers['Authorization']
        except KeyError as e:
            self.logger.warn("Request lacking Authorization header")
            self.token = ""

        self.header = {
            'Content-Type': self.return_mimetype,
            'Accept': self.return_mimetype,
            'Federation': 'false',
            'Authorization': self.token,
        }

        self.service_headers = {}
        self.timeout = timeout

    def announce_fed_out(self, request_type, destination, path):
        """
        Logging function to track requests being sent out by the Federation service

        :param request_type: The type of HTTP request to federate, either GET or POST. PUT TBD
        :type request_type: str
        :param destination: URL of service
        :type destination: str
        :param path: API endpoint of service
        :type path: Str
        """
        self.logger.info(json.dumps({"Sending": "{} -> {}/{}".format(
            request_type, destination, path
        )}))

    def announce_fed_in(self, source, code):
        """
        Logging function to track requests received by Federation from CanDIG services

        :param source: URL of service sending the response
        :type source: str
        :param code: Response code
        :type code: int
        """
        self.logger.info(json.dumps({"Received": "{} From {}".format(
            code, source
        )}))


    def get_service(self, url, endpoint_path, endpoint_payload):
        """
        Sends a GET request to service specified by url, adds response to self.status and self.results

        :param url: URL of service sending the response
        :param endpoint_path: Specific API endpoint of CanDIG service to be queried, may contain query string if GET
        :type endpoint_path: str
        :param endpoint_payload: Query parameters needed by endpoint specified in endpoint_path
        :type endpoint_payload: object, {param0=value0, paramN=valueN} for GET
        """
        try:
            request_handle = requests.Session()
            full_path = "{}/{}".format(url, endpoint_path)

            # self.announce_fed_out("GET", url, endpoint_path)

            resp = request_handle.get(full_path, headers=self.header, params=endpoint_payload, timeout=self.timeout)
            self.status.append(resp.status_code)
            self.result['response'] = resp.json()
            self.result['status'] = resp.status_code

        except requests.exceptions.ConnectionError:
            self.status.append(404)
            self.result['response'] = 'Connection Error. Peer server may be down.'
            self.result['status'] = 404
            return
        except requests.exceptions.Timeout:
            self.status.append(504)
            self.result['response'] = 'Peer server timed out, it may be down.'
            self.result['status'] = 504
            return
        except AttributeError as e:
            self.status.append(500)
            self.result['response'] = str(e)
            self.result['status'] = 500
            return

    def federate_check(self):
        """Checks if Federation conditions are met

        :return: Boolean
        """
        if 'Federation' in self.request_dict.headers and \
                self.request_dict.headers.get('Federation').lower() == 'false':
            return False
        else:
            return True

    def get_peer_from_url(self, peer_url):
        """
        Returns the peer name from the peer_url

        :param peer_url: URL of service
        :type peer_url: str
        :return: str
        """
        for peer, url in APP.config["peers"].items():
            if url == peer_url:
                return peer

    def post_service(self, url, endpoint_path, endpoint_payload):
        """
        Sends a POST request to service specified by url, adds response to self.status and self.results

        :param url: URL of service sending the response
        :param endpoint_path: Specific API endpoint of CanDIG service to be queried, may contain query string if GET
        :type endpoint_path: str
        :param endpoint_payload: Query parameters needed by endpoint specified in endpoint_path
        :type endpoint_payload: object, JSON struct dependent on service endpoint for POST
        """
        peer = self.get_peer_from_url(url)
        self.results[peer] = {}

        try:
            request_handle = requests.Session()
            full_path = "{}/{}".format(url, endpoint_path)
            # self.announce_fed_out("POST", url, endpoint_path, endpoint_payload)
            resp = request_handle.post(full_path, headers=self.header, json=endpoint_payload)
            self.status.append(resp.status_code)

            self.result['response'] = resp.json()
            self.result['status'] = resp.status_code

        except requests.exceptions.ConnectionError:
            self.status.append(404)
            self.result['response'] = 'Connection Error. Peer server may be down.'
            self.result['status'] = 404
            return
        except requests.exceptions.Timeout:
            self.status.append(504)
            self.result['response'] = 'Peer server timed out, it may be down.'
            self.result['status'] = 504
            return
        except AttributeError as e:
            self.status.append(500)
            self.result['response'] = str(e)
            self.result['status'] = 500
            return

    def handle_peer_request(self, request, endpoint_path, endpoint_payload, endpoint_service, header):
        """
        Make peer data requests and update the results and status for a FederationResponse

        If a response from a peer is received, it will be a Response Object with key pairs
            {"results":{"p1": {"status": 200, "response": [1, 2, 3]}}}, "service": "name" }

        Clients should be aware that the response from each peer server is returned as is, 
        meaning the data structure of the response is not known ahead of time.

        Clients are also advised to check for status code before proceeding.

        :param request: The type of HTTP request to federate, either GET or POST. PUT TBD
        :type request: str
        :param endpoint_path: Specific API endpoint of CanDIG service to be queried, may contain query string if GET
        :type endpoint_path: str
        :param endpoint_payload: Query string or data needed by endpoint specified in endpoint_path
        :type endpoint_payload: object, {param0=value0, paramN=valueN} for GET, JSON struct dependent on service endpoint for POST
        :param endpoint_service: Specific microservice name, should match a service listed in services.json config
        :type endpoint_service: str
        :param header: Request headers defined in self.headers
        :type header: object
        :return: List of ResponseObjects, this specific return is used only in testing
        """

        uri_list = []

        for peer in APP.config["peers"].values():
            uri_list.append("{}".format(peer))

        for future_response in self.async_requests(url_list=uri_list,
                                                   request=request,
                                                   header=header,
                                                   endpoint_payload=endpoint_payload,
                                                   endpoint_path=endpoint_path,
                                                   endpoint_service=endpoint_service):

            
            try:
                self.status.append(200)
                response = future_response["data"].result()
                self.results[future_response['peer']] = {}
                self.results[future_response['peer']]['status'] = response.status_code
                self.results[future_response['peer']]['response'] = response.json()['response']
            except AttributeError:
                if isinstance(future_response["data"], requests.exceptions.ConnectionError):
                    self.status.append(404)
                if isinstance(future_response["data"], requests.exceptions.Timeout):
                    self.status.append(504)
                continue
            except requests.exceptions.ConnectionError:
                self.status.append(404)
                self.results[future_response['peer']] = {}
                self.results[future_response['peer']]['status'] = 404
                self.results[future_response['peer']]['response'] = 'Connection Error. Peer server may be down.'
                continue

            except requests.exceptions.Timeout:
                self.status.append(504)
                self.results[future_response['peer']] = {}
                self.results[future_response['peer']]['status'] = 404
                self.results[future_response['peer']]['response'] = 'Peer server timed out, it may be down.'
                continue

        # Return is used for testing individual methods
        return self.results

    def async_requests(self, url_list, request, endpoint_path, endpoint_payload, endpoint_service, header):
        """Send requests to each CanDIG node in the network asynchronously using FutureSession. The
        futures are returned back to and handled by handle_peer_requests()


        :param url_list: List of
        :param request: The type of HTTP request to federate, either GET or POST. PUT TBD
        :type request: str
        :param endpoint_path: Specific API endpoint of CanDIG service to be queried, may contain query string if GET
        :type endpoint_path: str
        :param endpoint_payload: Query string or data needed by endpoint specified in endpoint_path
        :type endpoint_payload: object, {param0=value0, paramN=valueN} for GET, JSON struct dependent on service endpoint for POST
        :param endpoint_service: Specific microservice name, should match a service listed in services.json config
        :type endpoint_service: str
        :param header: Request headers defined in self.headers
        :type header: object
        :return: List of Futures
        """

        args = {"request_type": request, "endpoint_path": endpoint_path, "endpoint_payload": endpoint_payload, "endpoint_service": endpoint_service}
        async_session = FuturesSession(max_workers=10)  # capping max threads
        future_responses = []

        for url in url_list:
            future_resp = {}
            peer = self.get_peer_from_url(url)
            try:
                future_resp["peer"] = peer
                future_resp["data"] = async_session.post(url,
                                                    json=args, headers=header, timeout=self.timeout)
                future_responses.append(future_resp)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                future_resp["peer"] = peer
                future_resp["data"] = e
                future_responses.append(future_resp)

        return future_responses

    def merge_status(self, statuses):
        """Returns a single status to represent the federated query.

        Priority List:
        1. Return 200 if one exists within the list
        2. 201 > 405 > 504 > 404 > 500

        :param statuses: List of integer response codes
        :type statuses: list
        :return: Single response code
        :rtype: int
        """

        if len(statuses) == 1:
            return statuses[0]

        elif 200 in statuses:
            return 200

        elif 201 in statuses:
            return 201

        elif 405 in statuses:
            return 405
    
        elif 504 in statuses:
            return 504

        elif 404 in statuses:
            return 404

        elif 500 in statuses:
            return 500

        else:
            return 500

    def get_response_object(self):
        """Driver method to communicate with other CanDIG nodes.

        1. Check if federation is needed
        1a. Broadcast if needed
        2. If no federation is required, pass endpoint to service
        3. Aggregate and return all the responses.

        :return: response_object, Status
        :rtype: object, int
        """

        if self.request == "GET":

            if self.federate_check():

                self.handle_peer_request(request="GET",
                                         endpoint_path=self.endpoint_path,
                                         endpoint_payload=self.endpoint_payload,
                                         endpoint_service=self.endpoint_service,
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
                                         endpoint_service=self.endpoint_service,
                                         header=self.header)
            else:
                self.post_service(url=self.url,
                                  endpoint_path=self.endpoint_path,
                                  endpoint_payload=self.endpoint_payload)

        status = self.merge_status(self.status)

        if self.federate_check():
            response = {"results": self.results, "service": self.endpoint_service}
        else:
            response = {"response": self.result["response"], "service": self.endpoint_service}
   
        return response, status
