"""

Provides methods to handle both local and federated requests
"""


import json
import requests
from flask import current_app
from requests_futures.sessions import FuturesSession

APP = current_app


class ConnectivityCheck:
    """

    This is a collection of methods to facilitate federated queries across the CanDIG network

    :param request_dict: Flask request object to be modified and forwarded along to service
    :type request_dict: Flask.Request
    :param return_mimetype: HTTP content-type, default is application/json
    :type return_mimetype: str
    :param timeout: Wait time before a request times out, default is 5 seconds
    :type timeout: int
    """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-arguments


    def __init__(self, request_dict, return_mimetype='application/json', timeout=5):
        """Constructor method
        """
        self.results = []
        self.status = []
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


    # def get_service(self, url, endpoint_path, endpoint_payload):
    #     """
    #     Sends a GET request to service specified by url, adds response to self.status and self.results

    #     :param url: URL of service sending the response
    #     :param endpoint_path: Specific API endpoint of CanDIG service to be queried, may contain query string if GET
    #     :type endpoint_path: str
    #     :param endpoint_payload: Query parameters needed by endpoint specified in endpoint_path
    #     :type endpoint_payload: object, {param0=value0, paramN=valueN} for GET
    #     """
    #     try:
    #         request_handle = requests.Session()
    #         full_path = "{}/{}".format(url, endpoint_path)

    #         # self.announce_fed_out("GET", url, endpoint_path)

    #         resp = request_handle.get(full_path, headers=self.header, params=endpoint_payload, timeout=self.timeout)
    #         self.status.append(resp.status_code)


    #         if isinstance(resp.json(), list):
    #             self.results.extend(resp.json())
    #             # self.announce_fed_in(full_path, resp.status_code, resp.json())
    #         else:
    #             # Only take the 'data' portion of the Response

    #             response = [{key: value for key, value in resp.json().items() if key.lower()
    #                          not in ['headers', 'url']}]
    #             # self.announce_fed_in(full_path, resp.status_code, response)
    #             self.results.extend(response)

    #     except requests.exceptions.ConnectionError:
    #         self.status.append(404)
    #         return
    #     except requests.exceptions.Timeout:
    #         self.status.append(504)
    #         return
    #     except AttributeError as e:
    #         self.status.append(500)
    #         print(e)
    #         return

    # def federate_check(self):
    #     """Checks if Federation conditions are met

    #     :return: Boolean
    #     """
    #     if 'Federation' in self.request_dict.headers and \
    #             self.request_dict.headers.get('Federation').lower() == 'false':
    #         return False
    #     else:
    #         return True



    def handle_peer_request(self, header):
        """
    
        :param header: Request headers defined in self.headers
        :type header: object
        """

        uri_list = []

        for peer in APP.config["peers"].values():
            uri_list.append("{}/ping".format(peer))

        for future_response in self.async_requests(url_list=uri_list, header=header):
            try:
                response = future_response.result()
                self.results.extend([{"status": response.status_code, "url": response.url}])

            except AttributeError:
                if isinstance(future_response, requests.exceptions.ConnectionError):
                    self.results.extend([{"status": 404, "url": response.url}])
                if isinstance(future_response, requests.exceptions.Timeout):
                    self.results.extend([{"status": 504, "url": response.url}])

                continue
            except requests.exceptions.ConnectionError:
                    self.results.extend([{"status": 404, "url": response.url}])
                    continue

            except requests.exceptions.Timeout:
                    self.results.extend([{"status": 504, "url": response.url}])
                    continue


    def async_requests(self, url_list, header):
        """Send requests to each CanDIG node in the network asynchronously using FutureSession. The
        futures are returned back to and handled by handle_peer_requests()


        :param url_list: List of URLs to send requests
        :type url_list: array
        :param header: Request headers defined in self.headers
        :type header: object
        :return: List of Futures
        """

        async_session = FuturesSession(max_workers=10)  # capping max threads
        responses = []

        for url in url_list:
            try:
                # self.announce_fed_out(request_type, url, endpoint_path, endpoint_payload)
                responses.append(async_session.get(url, headers=header, timeout=self.timeout))
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                responses.append(e)

        return responses


    def check_connectivity(self):
        """Driver method to check CanDIG node connectiveness.
        """


        self.handle_peer_request(header=self.header)
        self.logger.info("Starting Federation peer connectivity check\n")
        for result in self.results:
            if result['status'] == 200:
                self.logger.info("{}: Successful\n".format(result['url']))
            else:
                self.logger.warn("{}: Error. Code {}\n".format(result['url'], result['status']))

        return {"status": 200, "results": self.results, "service": "Federation"}



