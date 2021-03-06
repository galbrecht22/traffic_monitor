from models.Stop import Stop
from models.Station import Station
import json
from datetime import datetime, timedelta
from math import ceil
from threading import Thread


class StopController:
    def __init__(self):
        self.stations = []
        self.updated_ids = set()
        self.thread_segment_size = 500

    def fetch_updates(self):
        # print(self.updated_ids)
        result = [station.toMongo() for station in self.stations if station.station_id in self.updated_ids]
        # print(json.dumps(result, ensure_ascii=False, indent=4))
        self.updated_ids = set()
        return result

    def toStopTripView(self, trip, stop_time):
        stopTripObject = trip.toMongo()
        keys_to_remove = ('departure_time', 'stop_times', 'next_stop_index', 'next_stop_name', 'state', 'latest_update')
        for k in keys_to_remove:
            stopTripObject.pop(k, None)
        stopTripObject['arrival_time'] = stop_time.actual_time
        stopTripObject['delay_delta'] = stop_time.delay_delta
        return stopTripObject

    def update(self, stop_time, trip):
        # print("StopTime.station_id: " + stop_time.station_id)
        station = next((station for station in self.stations if station.station_id == stop_time.station_id), None)
        if not station:
            station = Station(station_id=stop_time.station_id,
                              station_name=stop_time.stop_name,
                              stops=[Stop(stop_id=stop_time.stop_id,
                                          stop_name=stop_time.stop_name,
                                          station_id=stop_time.station_id,
                                          trips=[self.toStopTripView(trip, stop_time)])])
            # print("Station_id: " + station.station_id)
            self.stations.append(station)
        else:
            stop = next((stop for stop in station.stops if stop.stop_id == stop_time.stop_id), None)
            if not stop:
                station.stops.append(Stop(stop_id=stop_time.stop_id,
                                          stop_name=stop_time.stop_name,
                                          station_id=stop_time.station_id,
                                          trips=[self.toStopTripView(trip, stop_time)]))
            else:
                stopTrip = self.toStopTripView(trip, stop_time)
                stop.trips.append(stopTrip)
                stop.current_delays.append(
                    {'timestamp': stopTrip['arrival_time'], 'delay_delta': stopTrip['delay_delta']})
                stop.maxDelta = max(stop.maxDelta, stopTrip['delay_delta'])
                stop.avgDelta = round(
                    (sum([delta['delay_delta'] for delta in stop.current_delays]) / len(stop.current_delays)), 0)
                station.maxDelta = max(stop.maxDelta, station.maxDelta)
                station.avgDelta = round(sum([stop.avgDelta for stop in station.stops]) /
                                         len(station.stops), 0)
        self.updated_ids.add(station.station_id)
        # print(self.updated_ids)

    def refresh_current_delays(self):
        actual_date = datetime.now()
        actual_date -= timedelta(minutes=30)
        for station in self.stations:
            for stop in station.stops:
                stop.current_delays = [delay for delay in stop.current_delays if delay['timestamp'] > actual_date]
                stop.maxDelta = max([0, *[delay['delay_delta'] for delay in stop.current_delays]])
                stop.avgDelta = round(
                    (sum([delta['delay_delta'] for delta in stop.current_delays]) / max(1, len(stop.current_delays))), 0)
            station.maxDelta = max([0, *[stop.maxDelta for stop in station.stops]])
            station.avgDelta = round(sum([stop.avgDelta for stop in station.stops]) /
                                     max(len(station.stops), 1), 0)

        return [station.toMongo() for station in self.stations]

    def update_stations(self):
        return self.refresh_current_delays()

    def restore(self, records):
        N = int(ceil(len(records) / self.thread_segment_size))
        threads = []
        for n in range(N):
            t = Thread(target=self.restore_segment,
                       args=(records[(self.thread_segment_size * n):(self.thread_segment_size * (n + 1))],))
            t.start()
            threads.append(t)

        print(f"INFO:\t{N} threads started.")
        for t in threads:
            t.join()
        print(f"INFO:\tRestoring {len(records)} stations finished.")

    def restore_segment(self, segment):
        for station_record in segment:
            # stops = []
            # for stop in station_record.get('stops'):
            #     stops.append(Stop(stop_id=stop.get('stop_id'),
            #                       stop_name=stop.get('stop_name'),
            #                       trips=stop.get('trips')))
            stops = [Stop(stop_id=stop.get('stop_id'),
                          stop_name=stop.get('stop_name'),
                          station_id=stop.get('station_id'),
                          trips=stop.get('trips')) for stop in station_record.get('stops')]
            self.stations.append(Station(station_id=station_record.get('station_id'),
                                         station_name=station_record.get('station_name'),
                                         stops=stops))
