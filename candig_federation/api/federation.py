"""

Provides methods to handle both local and federated requests
"""

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

    def __init__(self, request, url, endpoint_path, endpoint_payload, request_dict, return_mimetype='application/json',
                 timeout=5):
        self.results = []
        self.status = []
        self.request = request
        self.url = url
        self.endpoint_path = endpoint_path
        self.endpoint_payload = endpoint_payload
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
        self.logger.info("Federation Service: {} -> {}/{}. Args: {}".format(
            request_type, destination, path, args
        ))
    
    def announce_fed_in(self, source, code, response):
        self.logger.info("Received {} From {}@{}. Data: {}".format(
            code, self.service_headers['X-Source'], source, response
        ))


    def get_service(self, url, endpoint_path, endpoint_payload):
        """

        make local data request and set the results and status for a FederationResponse
        """
        try:
            request_handle = requests.Session()
            full_path = "{}/{}".format(url, endpoint_path)
            self.announce_fed_out("GET", url, endpoint_path, endpoint_payload)
            resp = request_handle.get(full_path, headers=self.header, params=endpoint_payload, timeout=self.timeout)
            self.service_headers['X-Source'] = resp.headers['X-Source']
            self.status.append(resp.status_code)

            if isinstance(resp.json(), list):
                self.results.extend(resp.json())
                self.announce_fed_in(full_path, resp.status_code, resp.json())
            else:
                # Only take the 'data' portion of the Response
                response = [{key: value for key, value in resp.json().items() if key.lower()
                            not in ['headers', 'url']}]
                self.announce_fed_in(full_path, resp.status_code, response)
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
            self.announce_fed_out("POST", url, endpoint_path, endpoint_payload)
            resp = request_handle.post(full_path, headers=self.header, json=endpoint_payload)
            print("\n\n\n\n\n")
            print(resp.headers)
            self.service_headers['X-Source'] = resp.headers['X-Source']
            self.status.append(resp.status_code)

            if isinstance(resp.json(), list):
                self.results.extend(resp.json())
                self.announce_fed_in(full_path, resp.status_code, resp.json())


            else:
                # Only take the 'data' portion of the Response
                response = [{key: value for key, value in resp.json().items() if key.lower()
                            not in ['headers', 'url', 'args', 'json']}]
                self.announce_fed_in(full_path, resp.status_code, resp.json())
                self.results.extend(response)

        except requests.exceptions.ConnectionError:
            self.status.append(404)
            return

        except requests.exceptions.Timeout:
            self.status.append(408)
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

        # Old logic when using "local" peers vs uniform handling

        # for peer in APP.config["peers"].values():
        #     if peer != APP.config["local"]:
        #         uri_list.append("{}".format(peer))

        for peer in APP.config["peers"].values():
                uri_list.append("{}".format(peer))

        # self.logger.info("Federating: {}".format(uri_list))
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

        # if self.results:
        #     self.merge_counts()

    # def merge_counts(self):
    #     """
    #     merge federated counts and set results for FederationResponse
    #     TODO: Fully Implement this
    #     """
    #
    #     table = list(set(self.results.keys()))
    #     prepare_counts = {}
    #
    #     for record in self.results:
    #         for key, value in record.items():
    #             if key in prepare_counts:
    #                 prepare_counts[key].append(Counter(value))
    #             else:
    #                 prepare_counts[key] = [Counter(value)]
    #
    #     merged_counts = {}
    #     for field in prepare_counts:
    #         count_total = Counter()
    #         for count in prepare_counts[field]:
    #             count_total = count_total + count
    #         merged_counts[field] = dict(count_total)
    #     self.results[table] = [merged_counts]

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
                    self.announce_fed_out(request_type, uri, endpoint_path, endpoint_payload)
                    responses.append(async_session.get(uri,
                                                       headers=header, params=args, timeout=self.timeout))
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    responses.append(e)
        elif request_type == "POST":
            for uri in uri_list:
                try:
                    self.announce_fed_out(request_type, uri, endpoint_path, endpoint_payload)
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

        print(statuses)

        if len(statuses) == 1:
            return statuses[0]

        if 200 in statuses:
            return 200

        if 201 in statuses:
            return 201
        
        if 405 in statuses:
            return 405

        if 500 in statuses:
            return 500

        if 504 in statuses:
            return 504

        if 404 in statuses:
            return 404

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
                # self.logger.info("Federating POST")
                self.handle_peer_request(request="POST",
                                         endpoint_path=self.endpoint_path,
                                         endpoint_payload=self.endpoint_payload,
                                         header=self.header)
            else:
                self.post_service(url=self.url,
                                  endpoint_path=self.endpoint_path,
                                  endpoint_payload=self.endpoint_payload)
        
        try:
            response = {"status": self.merge_status(self.status), "results": sorted(list(set(self.results)))}

        except TypeError:
            # Dealing with dicts objects
            print("TE IN MERGING")
            print(self.results)
            response = {"status": self.merge_status(self.status), "results": self.results}
        
        self.logger.info(response)
        return response, self.service_headers