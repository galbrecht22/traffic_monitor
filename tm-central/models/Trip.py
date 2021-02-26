import json
from datetime import datetime, date, time
from typing import List
from .StopTime import StopTime
from .TripState import TripState
from json import JSONEncoder


class TripEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            serial = o.strftime('%Y-%m-%d %H:%M:%S')
            return serial
        if isinstance(o, date):
            serial = o.strftime('%Y-%m-%d')
            return serial
        if isinstance(o, time):
            serial = o.strftime('%H:%M:%S')
            return serial
        return o.__dict__


class TripEncoderNew(JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date, time)):
            return o.isoformat()
        return o.__dict__


class Trip:
    def __init__(self,
                 trip_id: str, route_id: str, route_name: str,
                 departure_time: str, destination: str,
                 stop_times: List[StopTime], location: [float]):
        self.trip_id = trip_id
        self.route_id = route_id
        self.route_name = route_name
        self.departure_time = departure_time
        self.destination = destination
        self.delay = 0
        self.stop_times = stop_times
        self.location = location
        self.next_stop_index = 0
        self.next_stop_name = stop_times[0].stop_name
        self.state = TripState.ONGOING
        self.latest_update = datetime.now()

    def toJSON(self):
        tripJSONData = json.dumps(self, cls=TripEncoder, indent=4, ensure_ascii=False)
        return tripJSONData

    def toMongo(self):
        tripJSONData = json.dumps(self, cls=TripEncoder, indent=4, ensure_ascii=False)
        tripJSON = json.loads(tripJSONData)

        # Reset datetime strings to datetime format
        tripJSON['departure_time'] = datetime.fromisoformat(tripJSON['departure_time'])
        tripJSON['latest_update'] = datetime.fromisoformat(tripJSON['latest_update'])
        for stop_time in tripJSON['stop_times']:
            stop_time['reference_time'] = datetime.fromisoformat(stop_time['reference_time'])
            stop_time['actual_time'] = datetime.fromisoformat(stop_time['actual_time'])

        return tripJSON

    def __str__(self):
        return self.toJSON()
