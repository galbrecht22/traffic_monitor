from datetime import datetime
import json


class StopTime:
    def __init__(self, stop_id: str, stop_name: str, station_id: str,
                 ref_timestamp: int, actual_timestamp: int,
                 is_next: bool, is_predicted: bool):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.station_id = station_id
        self.reference_timestamp = ref_timestamp
        self.actual_timestamp = actual_timestamp
        self.reference_time = datetime.fromtimestamp(self.reference_timestamp)
        self.actual_time = datetime.fromtimestamp(self.actual_timestamp)
        # self.location = location
        self.delay = max(0, self.actual_timestamp - self.reference_timestamp)
        self.delay_delta = 0
        self.is_next = is_next
        self.is_predicted = is_predicted
