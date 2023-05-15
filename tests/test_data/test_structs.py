"""
MockResponse: Functions like a regular Response from Requests
MockResponseInternal: Responses which are accessed in within handle_server_requests
    have already been modified by the time they are received.
"""

import json


class MockResponse:
    def __init__(self, json_data, status_code, headers={}):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = {'X-Source': '2222'}
        self.text = "response"

    def json(self):
        return self.json_data

    def status_code(self):
        return self.status_code

    def headers(self):
        return self.headers


# Internal Response needs a result() function since it's supposed to be a Future response

class MockResponseInternal:
    def __init__(self, json_data, status_code, headers={}):
        self.json_data = json_data
        self.status_code = status_code
        self.headers = {'X-Source': '2222'}
        self.text = "response"

    def json(self):
        return {"results": self.json_data,
                "status": self.status_code}

    def headers(self):
        return self.headers

    def result(self):
        return MockResponseInternal(self.json_data, self.status_code)


class testHeader():
    def __init__(self, headers):
        self.headers = headers

    def headers(self):
        return self.headers


exampleHeaders = testHeader({
    "Content-Type": "application/json",
    "Host": "ga4ghdev01.bcgsc.ca:8890",
    "User-Agent": "python-requests/2.22.0",
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsI",
    "Federation": "false"
})

fedHeader = testHeader({
    "Content-Type": "application/json",
    "Host": "ga4ghdev01.bcgsc.ca:8890",
    "User-Agent": "python-requests/2.22.0",
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsI",
    "Federation": "true"
})


TestParams = {
    "URI": "10.9.208.132",
    "PORT0": "8890",
    "PORT1": "8891",
    "PORT2": "8892",
    "Headers": exampleHeaders,
    "Federate": fedHeader,
    "Tyk1": "10.9.208.132:6000/v1/fanout",
    "Tyk2": "10.9.208.132:8000/v1/fanout",
    "Tyk3": "10.9.208.132:9000/v1/fanout",
    "path": "rnaget/projects",
    "service": "rnaget",
}

GetListV1 = {"projects": {"k1": "v1", "k2": "v2"}}
GetListV2 = {"projects": {"key1": "value1"}}
GetListV3 = {"projects": {"keyA": "valueB"}}

GetResponse = {
    "s1": MockResponse(GetListV1, 200),
    "s2": MockResponse(GetListV2, 200),
    "s3": MockResponse(GetListV3, 200),
    "i1": MockResponseInternal(GetListV1, 200),
    "i2": MockResponseInternal(GetListV2, 200),
    "i3": MockResponseInternal(GetListV3, 200),
    "timeout": MockResponseInternal({}, 408),
    "fail": MockResponseInternal(None, 404),
    "loc1": {"results": GetListV1, "location": {"name": "loc1", "province": "ON", "province-code": "ca-on"}},
    "loc2": {"results": GetListV2, "location": {"name": "loc2", "province": "ON", "province-code": "ca-on"}},
    "loc3": {"results": GetListV3, "location": {"name": "loc3", "province": "ON", "province-code": "ca-on"}},
    "j1": GetListV1
}


PostListM1 = {
    "data": [
        {
            "id": "WytHH1",
            "name": "mock1",
            "desc": "METADATA SERVER"
        },
        {
            "id": "WytHH2",
            "name": "mock2",
            "desc": "METADATA SERVER"
        }
    ]
}


PostListV1 = {
    "data": [
        {
            "id": "PLVE11",
            "name": "mockV11",
            "desc": "VARIANT SERVER"
        },
        {
            "id": "PLVE12",
            "name": "mockV12",
            "desc": "VARIANT SERVER"
        }
    ]
}

PostListV2 = {
    "data": [
        {
            "id": "PLVE21",
            "name": "mockV21",
            "desc": "VARIANT SERVER"
        },
        {
            "id": "PLVE22",
            "name": "mockV22",
            "desc": "VARIANT SERVER"
        }
    ]
}

PostListV3 = {
    "data": [
        {
            "id": "PLVE31",
            "name": "mockV31",
            "desc": "VARIANT SERVER"
        },
        {
            "id": "PLVE32",
            "name": "mockV32",
            "desc": "VARIANT SERVER"
        }
    ]
}

PostResponse = {
    "PLM1": MockResponse(PostListM1, 200),
    "PLV1": MockResponse(PostListV1, 200),
    "PLV2": MockResponse(PostListV2, 200),
    "iPLV1": MockResponseInternal(PostListV1, 200),
    "iPLV2": MockResponseInternal(PostListV2, 200),
    "PLV3": MockResponse(PostListV3, 200),
    "iPLV3": MockResponseInternal(PostListV3, 200),
    "timeout": MockResponseInternal(None, 408),
    "fail": MockResponseInternal(None, 404),
    "loc1": {"results": PostListV1, "location": {"name": "loc1", "province": "ON", "province-code": "ca-on"}},
    "loc2": {"results": PostListV2, "location": {"name": "loc2", "province": "ON", "province-code": "ca-on"}},
    "loc3": {"results": PostListV3, "location": {"name": "loc3", "province": "ON", "province-code": "ca-on"}}

}
