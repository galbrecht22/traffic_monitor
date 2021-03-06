import json
from json import JSONEncoder
from datetime import datetime, date, time


class StationEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date, time)):
            return o.isoformat()
        return o.__dict__


class Station:
    def __init__(self, station_id, station_name, stops):
        self.station_id = station_id
        self.station_name = station_name
        self.maxDelta = 0
        self.avgDelta = 0
        self.stops = stops


    def toMongo(self):
        stationJSONData = json.dumps(self, cls=StationEncoder, indent=4, ensure_ascii=False)
        stationJSON = json.loads(stationJSONData)

        for stop in stationJSON['stops']:
            for trip in stop['trips']:
                trip['arrival_time'] = datetime.fromisoformat(trip['arrival_time'])

        return stationJSON
