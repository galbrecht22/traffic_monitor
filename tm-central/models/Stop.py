
class Stop:
    def __init__(self, stop_id, stop_name, station_id, trips):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.station_id = station_id
        self.maxDelta = 0
        self.avgDelta = 0
        self.trips = trips
        self.current_delays = []
