import json

from src.configuration import Configuration
from src.api import APIHelper
from src.models import VisitorHolder, Event
from src.exceptions import ApiError

class Client:

    def __init__(self, api_key=None, dataset_endpoint=None, submit_endpoint=None):
        self.config = Configuration(api_key, dataset_endpoint, submit_endpoint)
        self._api = APIHelper(self.config.API_KEY)
        self._visitors = VisitorHolder()
        self._results = {"sessionsByUser": {}}
        self._data = {"events": []}

    @property
    def api(self):
        return self._api

    @property
    def visitors(self):
        return self._visitors

    @property
    def results(self):
        return self._results

    @property
    def data(self):
        return self._data

    def retrieve_data(self):
        resp = self.api.get("https://candidate.hubteam.com/candidateTest/v3/problem/dataset?userKey=1c4024086f23287e651adb18b958")
        if resp.status_code >= 300:
            message = "GET call to dataset endpoint returned status_code {0}. Message: {1}".format(resp.status_code,resp.content)
            raise ApiError(message)
        data = resp.json()
        data["events"].sort(key=lambda event: event['timestamp'])
        data["events"] = [Event(**event) for event in data["events"]]
        self._data["events"] = data["events"]

    def ingest_data(self):
        for event in self.data['events']:
            self.visitors.add_event(event)

    def submit_data(self):
        resp = self.api.post("https://candidate.hubteam.com/candidateTest/v3/problem/result?userKey=1c4024086f23287e651adb18b958",
                             data=json.dumps(self.results))
        if resp.status_code >= 300:
            message = "POST call to submit endpoint returned status_code {0}. Message: {1}".format(resp.status_code,resp.content)
            raise ApiError(message)
        return resp

    def wrangle_output(self):
        output = self.results['sessionsByUser']
        for visitor, sessions in self.visitors.items():
            output[visitor] = sessions.to_dictionary()
