class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def status_code(self):
        return self.status_code

    def results(self):
        return MockResponse(self.json_data, self.status_code)

    def result(self):
        return MockResponse(self.json_data, self.status_code)


class testHeader():
    def __init__(self, headers):
        self.headers = headers

    def headers(self):
        return self.headers

    def switchBool(self):
        self.headers["Federation"] = not self.headers["Federation"]


exampleHeaders = testHeader({
        "Content-Type": "application/json",
        "Host": "ga4ghdev01.bcgsc.ca:8890",
        "User-Agent": "python-requests/2.22.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsI",
        "Federation": "false"
    })



TESTING_PARAMS = {
    "URI": "10.9.208.132",
    "PORT0": "8890",
    "PORT1": "8891",
    "Headers": exampleHeaders,
    "Tyk1": "10.9.208.132:6000",
    "Tyk2": "10.9.208.132:8000"
}

ANSWER_PARAMS = {
    "s1": MockResponse({"projects": {"k1": "v1", "k2": "v2"}}, 200),
    "s2": MockResponse({"projects": {"key1": "value1"}}, 200),
    "fail": MockResponse(None, 404),
    "v1": {"projects": {"k1": "v1", "k2": "v2"}},
    "v2": {"projects": {"key1": "value1"}},
}



PostListM1 = {
    "results": [
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
    ],
    "status": 200
}

PostListV1 = {
    "results": [
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
    ],
    "status": 200
}

PostListV2 = {
    "results": [
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
    ],
    "status": 200
}

POST_RESPONSES = {
    "PLM1": PostListM1,
    "PLV1": PostListV1,
    "PLV2": PostListV2
}

