from datetime import datetime as dt
from time import time
from models.StopTime import StopTime
from models.Trip import Trip
from models.TripState import TripState
from math import ceil
from threading import Thread


class TripController:
    def __init__(self, api_connector):
        self.trips = []

        self.finishedDTO = []
        self.failedDTO = []
        self.createdDTO = []

        self.queued_ids = []
        self.inner_queued = 0
        self.outer_queued = 0

        self.thread_segment_size = 100
        self.api_connector = api_connector

    @staticmethod
    def create_error_record(trip_id: str, error_code: str, cause: str, description: str = None, snapshot=None):
        doc = {'trip_id': trip_id, 'cause': cause, 'code': error_code, 'time': dt.fromtimestamp(time())}
        if description:
            doc['description'] = description
        if snapshot:
            doc['snapshot'] = snapshot

        return doc

    @staticmethod
    def contains_trip(obj_list, trip_id):
        trip_ids = [trip['trip_id'] for trip in obj_list]
        return trip_id in trip_ids

    @staticmethod
    def auto_config_trip(trip):
        nb_stops = len(trip.stop_times)

        for i in range(nb_stops):
            if not trip.stop_times[i].is_predicted:
                # self.stop_times[i].update_stop()
                if i == nb_stops - 1:
                    trip.state = TripState.FINISHED
                else:
                    trip.next_stop_index += 1
                    trip.next_stop_name = trip.stop_times[i + 1].stop_name

    # Main functions
    def restore(self, trip_records):
        self.failedDTO = []
        N = int(ceil(len(trip_records) / self.thread_segment_size))
        threads = []
        for n in range(N):
            t = Thread(target=self.restore_segment,
                       args=(trip_records[(self.thread_segment_size * n):(self.thread_segment_size * (n + 1))],))
            t.start()
            threads.append(t)

        print(f"INFO:\t{N} threads started.")
        for t in threads:
            t.join()
        print("INFO:\tRestoring finished.")

        return len(self.trips), self.failedDTO

    def restore_segment(self, segment):
        for trip_record in segment:
            trip_id = trip_record.get('trip_id')
            response = self.api_connector.trip_details(trip_id="BKK_" + trip_id)
            if response.status_code != 200:
                print(f"ERROR:\t{response.json().get('text')} [{response.status_code}]")
                error_record = self.create_error_record(trip_id=trip_id,
                                                        error_code=response.status_code,
                                                        cause='restore',
                                                        description=response.json().get('text'),
                                                        snapshot=trip_record)
                self.failedDTO.append(error_record)

            else:
                stop_time_refs = trip_record.get('stop_times')
                stop_times = [StopTime(stop_id=stop_time_refs[i].get('stop_id'),
                                       stop_name=stop_time_refs[i].get('stop_name'),
                                       ref_timestamp=stop_time_refs[i].get('reference_timestamp'),
                                       actual_timestamp=stop_time_refs[i].get('actual_timestamp'),
                                       # location=trip_record.get('stop_times')[i].get('location'),
                                       is_predicted=stop_time_refs[i].get('is_predicted'),
                                       is_next=stop_time_refs[i].get('is_next'))
                              for i in range(len(stop_time_refs))]

                trip = Trip(
                    trip_id=trip_record.get('trip_id'),
                    route_id=trip_record.get('route_id'),
                    route_name=trip_record.get('route_name'),
                    departure_time=trip_record.get('departure_time'),
                    destination=trip_record.get('destination'),
                    stop_times=stop_times,
                    location=trip_record.get('location')
                )

                self.auto_config_trip(trip)

                self.trips.append(trip)

    def update(self):
        self.failedDTO, self.finishedDTO, self.queued_ids, self.inner_queued = [], [], [], 0

        N = int(ceil(len(self.trips) / self.thread_segment_size))
        threads = []
        for n in range(N):
            t = Thread(target=self.update_segment,
                       args=(self.trips[(self.thread_segment_size * n):(self.thread_segment_size * (n + 1))],))
            t.start()
            threads.append(t)

        print(f"INFO:\t{N} threads started.")
        for t in threads:
            t.join()
        print("INFO:\tUpdating RealTimeView finished.")

        self.trips[:] = [trip for trip in self.trips
                         if not self.contains_trip(self.finishedDTO, trip.trip_id)
                         and not self.contains_trip(self.failedDTO, trip.trip_id)]

        return ([trip.toMongo() for trip in self.trips if trip.trip_id not in self.queued_ids],
                self.finishedDTO,
                self.failedDTO,
                self.inner_queued)

    def update_segment(self, segment):
        for trip in segment:
            if trip.state == TripState.FINISHED:
                self.finishedDTO.append(trip.toMongo())
                continue
            response = self.api_connector.trip_details(trip_id="BKK_" + trip.trip_id)
            if response.status_code != 200:
                print(f"ERROR:\t{response.json().get('text')} [{response.status_code}]")
                error_record = self.create_error_record(trip_id=trip.trip_id,
                                                        error_code=response.status_code,
                                                        cause='update',
                                                        description=response.json().get('text'),
                                                        snapshot=trip.toMongo())
                self.failedDTO.append(error_record)
                continue

            trip_details = response.json()

            stop_times = trip_details.get('data').get('entry').get('stopTimes')

            if 'predictedDepartureTime' not in stop_times[0]:
                self.inner_queued += 1
                self.queued_ids.append(trip.trip_id)
                # TODO: Logging
                continue

            self.update_trip(trip, trip_details)

    def update_trip(self, trip, trip_details):
        # stop_offset = trip.next_stop_index
        nb_stops = len(trip.stop_times)
        trip.latest_update = dt.fromtimestamp(trip_details.get('currentTime') // 1000)
        if 'vehicle' in trip_details.get('data').get('entry'):
            trip.location = trip_details.get('data').get('entry').get('vehicle').get('location')
        else:
            trip.location = {'lat': None, 'lon': None}
        stop_times = trip_details.get('data').get('entry').get('stopTimes')

        assert len(stop_times) == nb_stops

        # Refresh all stop times in every update to achieve more accurate data
        trip.next_stop_index = 0
        trip.next_stop_name = trip.stop_times[0].stop_name

        # Update stop times
        # for i in range(stop_offset, nb_stops):
        for i in range(nb_stops):

            reference_time_str = 'departureTime' if i == 0 else 'arrivalTime'
            actual_time_str = 'predictedDepartureTime' if i == 0 else 'predictedArrivalTime'

            reference_timestamp = stop_times[i].get(reference_time_str)
            reference_time = dt.fromtimestamp(reference_timestamp)

            actual_timestamp = stop_times[i].get(actual_time_str)
            actual_time = dt.fromtimestamp(actual_timestamp)

            trip.stop_times[i].reference_timestamp = reference_timestamp
            trip.stop_times[i].reference_time = reference_time
            trip.stop_times[i].actual_timestamp = actual_timestamp
            trip.stop_times[i].actual_time = actual_time

            trip.stop_times[i].delay = max(
                0, trip.stop_times[i].actual_timestamp - trip.stop_times[i].reference_timestamp)

            if dt.timestamp(trip.latest_update) - dt.timestamp(actual_time) > 60:
                trip.stop_times[i].is_predicted = False
                if i == nb_stops - 1:
                    trip.state = TripState.FINISHED
                else:
                    trip.next_stop_index += 1
                    trip.next_stop_name = trip.stop_times[i + 1].stop_name
        trip.delay = trip.stop_times[trip.next_stop_index].delay

    def load(self, new_records):
        self.createdDTO, self.failedDTO, self.outer_queued = [], [], 0

        N = int(ceil(len(new_records) / self.thread_segment_size))
        threads = []
        for n in range(N):
            t = Thread(target=self.load_segment,
                       args=(new_records[(self.thread_segment_size * n):(self.thread_segment_size * (n + 1))],))
            t.start()
            threads.append(t)

        print(f"INFO:\t{N} threads started.")
        for t in threads:
            t.join()
        print("INFO:\tLoading new trips finished.")

        return self.createdDTO, self.failedDTO, self.outer_queued

    def load_segment(self, segment):
        """ Collect trips to load in RealTimeView MongoDB """

        def handle_error(response, trip_id):
            print(f"ERROR:\t{response.json().get('text')} [{response.status_code}]")
            error_record = self.create_error_record(trip_id=trip_id,
                                                    error_code=response.status_code,
                                                    cause='load',
                                                    description=response.json().get('text'))
            self.failedDTO.append(error_record)

        def build_trip(response, trip_id, route_id, route_name, destination, departure_time):
            trip_details = response.json()

            if 'vehicle' in trip_details.get('data').get('entry'):
                location = trip_details.get('data').get('entry').get('vehicle').get('location')
            else:
                location = {'lat': None, 'lon': None}

            stop_times_obj = trip_details.get('data').get('entry').get('stopTimes')
            current_time = trip_details.get('currentTime')
            stops_obj = trip_details.get('data').get('references').get('stops')
            stop_times = [StopTime(
                stop_id=stop_times_obj[i].get('stopId'),
                stop_name=stops_obj.get(stop_times_obj[i].get('stopId')).get('name'),
                ref_timestamp=stop_times_obj[i].get('arrivalTime') if i > 0 else stop_times_obj[i].get('departureTime'),
                actual_timestamp=stop_times_obj[i].get('predictedArrivalTime') if i > 0 else stop_times_obj[i].get(
                    'predictedDepartureTime'),
                # location={'lat': None, 'lon': None},
                is_predicted=True, is_next=False)
                for i in range(len(stop_times_obj))]
            return Trip(trip_id, route_id, route_name, departure_time, destination, stop_times, location)

        for record in segment:
            trip_id = record[2]

            response = self.api_connector.trip_details(trip_id="BKK_" + trip_id)
            if response.status_code != 200:
                handle_error(response, trip_id)
                continue

            if 'predictedDepartureTime' not in response.json().get('data').get('entry').get('stopTimes')[0]:
                self.outer_queued += 1
                continue

            route_id = record[0]
            route_name = record[1]
            destination = record[3]
            departure_time = record[4]

            trip = build_trip(response, trip_id, route_id, route_name, destination, departure_time)
            self.auto_config_trip(trip)

            self.trips.append(trip)
            self.createdDTO.append(trip.toMongo())

        # TODO: Logging
