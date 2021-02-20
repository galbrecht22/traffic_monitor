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
        self.update()

    def update(self, trip_details=None):
        stop_offset = self.next_stop_index
        nb_stops = len(self.stop_times)

        if not trip_details:
            # Auto-update mode
            for i in range(nb_stops):
                if not self.stop_times[i].is_predicted:
                    if i == nb_stops - 1:
                        self.state = TripState.FINISHED
                    else:
                        self.next_stop_index += 1
                        self.next_stop_name = self.stop_times[i + 1].stop_name
        else:
            self.latest_update = datetime.fromtimestamp(trip_details.get('currentTime') // 1000)
            if 'vehicle' in trip_details.get('data').get('entry'):
                self.location = trip_details.get('data').get('entry').get('vehicle').get('location')
            else:
                self.location = {'lat': None, 'lon': None}
            stop_times = trip_details.get('data').get('entry').get('stopTimes')

            assert len(stop_times) == nb_stops

            # Refresh all stop times in every update to achieve more accurate data
            self.next_stop_index = 0
            self.next_stop_name = self.stop_times[0].stop_name

            # Refresh stop times only from actual next stop
            # for i in range(stop_offset, nb_stops):

            for i in range(nb_stops):

                reference_time_str = 'departureTime' if i == 0 else 'arrivalTime'
                actual_time_str = 'predictedDepartureTime' if i == 0 else 'predictedArrivalTime'

                reference_timestamp = stop_times[i].get(reference_time_str)
                reference_time = datetime.fromtimestamp(reference_timestamp)

                actual_timestamp = stop_times[i].get(actual_time_str)
                actual_time = datetime.fromtimestamp(actual_timestamp)

                self.stop_times[i].reference_timestamp = reference_timestamp
                self.stop_times[i].reference_time = reference_time
                self.stop_times[i].actual_timestamp = actual_timestamp
                self.stop_times[i].actual_time = actual_time

                self.stop_times[i].delay = max(
                    0, self.stop_times[i].actual_timestamp - self.stop_times[i].reference_timestamp)

                if datetime.timestamp(self.latest_update) - datetime.timestamp(actual_time) > 60:
                    self.stop_times[i].is_predicted = False
                    if i == nb_stops - 1:
                        self.state = TripState.FINISHED
                    else:
                        self.next_stop_index += 1
                        self.next_stop_name = self.stop_times[i + 1].stop_name
        self.delay = self.stop_times[self.next_stop_index].delay

    def toJSON(self):
        tripJSONData = json.dumps(self, cls=TripEncoder, indent=4, ensure_ascii=False)
        return tripJSONData

    def toMongo(self):
        tripJSONData = json.dumps(self, cls=TripEncoder, indent=4, ensure_ascii=False)
        tripJSON = json.loads(tripJSONData)
        return tripJSON

    def __str__(self):
        return self.toJSON()
