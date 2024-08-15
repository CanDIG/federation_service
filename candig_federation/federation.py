"""

Provides methods to handle both local and federated requests
"""


import json
import requests
from requests_futures.sessions import FuturesSession
from network import get_registered_servers, get_registered_services
from candigv2_logging.logging import CanDIGLogger


logger = CanDIGLogger(__file__)


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

    def __init__(self, request, endpoint_path, endpoint_payload, request_dict, endpoint_service, return_mimetype='application/json',
                 timeout=60):
        """Constructor method
        """
        self.results = {}
        self.status = {}
        self.message = {}
        self.request = request
        self.endpoint_path = endpoint_path
        self.endpoint_payload = endpoint_payload
        self.endpoint_service = endpoint_service
        self.return_mimetype = return_mimetype
        self.request_dict = request_dict
        self.servers = get_registered_servers()
        self.services = get_registered_services()

        try:
            self.token = self.request_dict.headers['Authorization']
        except KeyError as e:
            logger.warning("Request lacking Authorization header")
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
        logger.info(json.dumps({"Sending": "{} -> {}/{}".format(
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
        logger.info(json.dumps({"Received": "{} From {}".format(
            code, source
        )}))

    def federate_check(self):
        """Checks if Federation conditions are met

        :return: Boolean
        """
        if 'Federation' in self.request_dict.headers and \
                self.request_dict.headers.get('Federation').lower() == 'false':
            return False
        else:
            return True

    def get_service(self, service, endpoint_path, endpoint_payload):
        """
        Sends a GET request to service, adds response to self.status and self.results

        :param service: name of service sending the response
        :param endpoint_path: Specific API endpoint of CanDIG service to be queried, may contain query string if GET
        :type endpoint_path: str
        :param endpoint_payload: Query parameters needed by endpoint specified in endpoint_path
        :type endpoint_payload: object, {param0=value0, paramN=valueN} for GET
        """
        try:
            request_handle = requests.Session()
            full_path = "{}/{}".format(self.services[service]['url'], endpoint_path)
            # self.announce_fed_out("GET", service, endpoint_path)

            resp = request_handle.get(
                full_path, headers=self.header, params=endpoint_payload, timeout=self.timeout)
            self.status = resp.status_code
            self.results = resp.json()
        except requests.exceptions.ConnectionError:
            self.status = 404
            self.message = 'Connection Error, peer server may be down.'
            return
        except requests.exceptions.Timeout:
            self.status = 504
            self.message = 'Peer server timed out, it may be down.'
            return
        except Exception as e:
            self.status = 500
            self.message = f"get_service: {type(e)} {str(e)}"
            return

    def post_service(self, service, endpoint_path, endpoint_payload):
        """
        Sends a POST request to service, adds response to self.status and self.results

        :param service: name of service sending the response
        :param endpoint_path: Specific API endpoint of CanDIG service to be queried, may contain query string if GET
        :type endpoint_path: str
        :param endpoint_payload: Query parameters needed by endpoint specified in endpoint_path
        :type endpoint_payload: object, JSON struct dependent on service endpoint for POST
        """
        try:
            request_handle = requests.Session()
            full_path = "{}/{}".format(self.services[service]['url'], endpoint_path)
            # self.announce_fed_out("POST", service, endpoint_path, endpoint_payload)
            resp = request_handle.post(
                full_path, headers=self.header, json=endpoint_payload)
            self.status = resp.status_code
            self.results = resp.json()
        except requests.exceptions.ConnectionError:
            self.status = 404
            self.message = 'Connection Error. Peer server may be down.'
            return
        except requests.exceptions.Timeout:
            self.status = 504
            self.message = 'Peer server timed out, it may be down.'
            return
        except Exception as e:
            self.status = 500
            self.message = f"post_service: {type(e)} {str(e)}"
            return

    def handle_server_request(self, request, endpoint_path, endpoint_payload, endpoint_service, header):
        """
        Make peer server data requests and update the results and status for a FederationResponse

        If a response from a peer server is received, it will be a Response Object with key pairs
            {"status": [], "message": [], "results": [], "service": "name" }

        The data structures within results are still unknown/undefined at this time, so
        just append everything instead of attempting to aggregate internal structs.

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
        future_responses = self.async_requests(request=request,
           header=header,
           endpoint_payload=endpoint_payload,
           endpoint_path=endpoint_path,
           endpoint_service=endpoint_service)

        for future_response_id in future_responses.keys():
            future_response = future_responses[future_response_id]
            location = future_response["location"]
            try:
                future_response = future_response["response"]
                response = future_response.result()

                # If the call was successful append the results
                if response.status_code in [200, 201]:
                    self.results[future_response_id] = response.json()['results']
                    self.status[future_response_id] = response.status_code
                elif response.status_code == 405:
                    self.status[future_response_id] = response.status_code
                    self.message[future_response_id] = f"Unauthorized: {response.text}"
                else:
                    self.status[future_response_id] = response.status_code
                    self.message[future_response_id] = f"handle_server_request failed on {future_response_id}, federation = {self.header['Federation']}"
            except AttributeError:
                if isinstance(future_response, requests.exceptions.ConnectionError):
                    self.status[future_response_id] = 404
                    self.message[future_response_id] = f'Connection Error. Peer server may be down. Location: {location["name"]}, {location["province"]}'
                if isinstance(future_response, requests.exceptions.Timeout):
                    self.status[future_response_id] = 504
                    self.message[future_response_id] = f'Peer server timed out, it may be down. Location: {location["name"]}, {location["province"]}'
                continue
            except requests.exceptions.ConnectionError:
                self.status[future_response_id] = 404
                self.message[future_response_id] = f'Connection Error. Peer server may be down. Location: {location["name"]}, {location["province"]}'
                continue
            except requests.exceptions.Timeout:
                self.status[future_response_id] = 504
                self.message[future_response_id] = f'Peer server timed out, it may be down. Location: {location["name"]}, {location["province"]}'
                continue
            except Exception as e:
                self.status[future_response_id] = 500
                self.message[future_response_id] = f"handle_server_request failed on {future_response_id}, federation = {self.header['Federation']}: {type(e)}: {str(e)} {response.text}"
                continue



        # Return is used for testing individual methods
        return self.results

    def async_requests(self, request, endpoint_path, endpoint_payload, endpoint_service, header):
        """Send requests to each CanDIG node in the network asynchronously using FutureSession. The
        futures are returned back to and handled by handle_server_requests()


        :param url_list: List of peer server URLs
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
        args = {"method": request, "path": endpoint_path,
                "payload": endpoint_payload, "service": endpoint_service}
        async_session = FuturesSession(max_workers=10)  # capping max threads
        responses = {}

        for server in self.servers.values():
            try:
                # self.announce_fed_out(request_type, url, endpoint_path, endpoint_payload)
                response = {}
                url = f"{server['server']['url']}/v1/fanout"
                response["response"] = async_session.post(url, json=args, headers=header, timeout=self.timeout)
                response["location"] = server['server']["location"]

                responses[server['server']['id']] = response

            except Exception as e:
                responses[server['server']['id']] = f"async_requests {server['server']['id']}: {type(e)} {str(e)}"

        return responses

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

                self.handle_server_request(request="GET",
                                           endpoint_path=self.endpoint_path,
                                           endpoint_payload=self.endpoint_payload,
                                           endpoint_service=self.endpoint_service,
                                           header=self.header)

            else:
                self.get_service(service=self.endpoint_service,
                                 endpoint_path=self.endpoint_path,
                                 endpoint_payload=self.endpoint_payload)
        else:

            if self.federate_check():
                self.handle_server_request(request="POST",
                                           endpoint_path=self.endpoint_path,
                                           endpoint_payload=self.endpoint_payload,
                                           endpoint_service=self.endpoint_service,
                                           header=self.header)
            else:
                self.post_service(service=self.endpoint_service,
                                  endpoint_path=self.endpoint_path,
                                  endpoint_payload=self.endpoint_payload)

        response = {
            "status": self.status,
            "results": self.results,
            "service": self.endpoint_service

        }
        status = self.status

        # If status is not an int, this is an aggregate result
        if "int" not in str(type(self.status)):
            status = self.merge_status(list(self.status.values()))

            if len(self.message.keys()) > 0:
                response['message'] = self.message
            # add locations:
            response['location'] = {}
            for server in self.servers:
                response['location'][server] = self.servers[server]['server']['location']

            # now deconvolute the result to an array:
            response_array = []
            for server in response['location'].keys():
                r = {
                    'location': response['location'][server],
                    'service': response['service']
                }
                if server in response['results']:
                    r['results'] = response['results'][server]
                if server in response['status']:
                    r['status'] = response['status'][server]
                if 'message' in response and server in response['message']:
                    r['message'] = response['message'][server]
                response_array.append(r)
            response = response_array
        return response, status
