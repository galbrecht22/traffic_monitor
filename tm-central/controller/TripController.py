from models.StopTime import StopTime
from models.Trip import Trip
from models.TripState import TripState
from models.TrafficAlert import TrafficAlert
from datetime import datetime
from time import sleep, time
from threading import Thread, enumerate
from math import ceil


class TripController:
    def __init__(self, api_connector, static_db, dynamic_db):
        self.api_connector = api_connector
        self.static_db = static_db
        self.dynamic_db = dynamic_db
        self.trips = []
        self.trip_ids = []
        self.errors = []
        self.update_counter = 0
        self.insert_counter = 0
        self.queue_counter = 0
        self.save_counter = 0
        self.load_error_counter = 0
        self.update_error_counter = 0
        self.trips_to_update = []
        self.trips_to_realtime = []
        self.trips_to_save = []
        self.trips_actual_errors = []
        self.trips_rt_errors = []
        self.segment_size = 100
        self.refresh_alerts_clock = 0

    def get_alerts(self):
        self.refresh_alerts_clock = int(time())
        response = self.api_connector.alert_search()
        details = response.json()
        alerts = []
        alert_ids = details.get('data').get('entry').get('alertIds')
        references = details.get('data').get('references')
        alert_references = references.get('alerts')
        route_references = references.get('routes')
        for i in alert_ids:
            alert_details = alert_references.get(i)
            alert_route_ids = [route_id for route_id in alert_details.get('routeIds') if route_id[4] in ['0', '1', '2']]
            alert_route_names = []
            for r in alert_route_ids:
                alert_route = route_references.get(r)
                if alert_route:
                    if alert_route.get('type') == 'BUS':
                        alert_route_names.append({'route_id': r, 'route_name': alert_route.get('shortName')})
            if len(alert_route_names) > 0:
                alerts.append(TrafficAlert(alert_details, alert_route_names))
        alert_docs = [alert.toJSON() for alert in alerts]

        delete_res = self.dynamic_db['traffic_alerts'].delete_many({})
        insert_res = self.dynamic_db['traffic_alerts'].insert_many(alert_docs)

    def execute_db_update(self):
        """ Update trips in RealTimeView MongoDB """
        if not self.trips_to_update:
            return
        for trip in self.trips_to_update:
            query = {"trip_id": trip.trip_id}
            new_values = {"$set": trip.toMongo()}
            update_res = self.dynamic_db['traffic_monitor_trip'].update_one(query, new_values)
            self.update_counter += 1
            assert update_res.modified_count == 1
        # TODO: Logging
        self.trips_to_update = []

    def execute_db_load(self):
        """ Move trips from ActualTrips MySQL to RealTimeView MongoDB """
        if not self.trips_to_realtime:
            return

        """ Insert trips to RealTimeView MongoDB """
        docs = [trip.toMongo() for trip in self.trips_to_realtime]
        insert_res = self.dynamic_db['traffic_monitor_trip'].insert_many(docs)
        self.insert_counter += len(insert_res.inserted_ids)

        """ Remove trips from ActualTrips MySQL """
        sql = """DELETE FROM actual_trips WHERE trip_id IN ({})"""
        vals = ["'" + trip.trip_id + "'" for trip in self.trips_to_realtime]
        with self.static_db.cursor() as cursor:
            cursor.execute(sql.format(','.join(vals)))
            self.static_db.commit()
        self.trips_to_realtime = []
        # assert len(insert_res.inserted_ids) == cursor.rowcount

    def execute_db_save(self):
        """ Move finished trips from RealTimeView MongoDB to FinishedTrips MongoDB """
        if not self.trips_to_save:
            return
        trip_ids = [trip.trip_id for trip in self.trips_to_save]
        docs = [trip.toMongo() for trip in self.trips_to_save]
        insert_res = self.dynamic_db['finished_buffer'].insert_many(docs)
        delete_res = self.dynamic_db['traffic_monitor_trip'].delete_many({'trip_id': {'$in': trip_ids}})
        # assert len(insert_res.inserted_ids) == len(delete_res.deleted_count)

        """ Remove finished trips from memory """
        for trip in self.trips_to_save:
            self.trips.remove(trip)
        self.save_counter += len(insert_res.inserted_ids)
        self.trips_to_save = []
        # TODO: Logging

    def execute_db_actual_errors(self):
        """ Remove trips with errors from ActualTrips MySQL """
        if not self.trips_actual_errors:
            return
        with self.static_db.cursor() as cursor:
            sql = """DELETE FROM actual_trips WHERE trip_id IN ({})"""
            vals = ["'" + trip_id + "'" for trip_id in self.trips_actual_errors]
            cursor.execute(sql.format(','.join(vals)))
            self.static_db.commit()
            self.load_error_counter += cursor.rowcount
        self.trips_actual_errors = []
        # TODO: Logging

    def execute_db_realtime_errors(self):
        """ Remove trips with errors from RealTimeView MongoDB """
        if not self.trips_rt_errors:
            return
        trip_ids = [trip.trip_id for trip in self.trips_rt_errors]
        docs = [trip.toMongo() for trip in self.trips_rt_errors]
        delete_res = self.dynamic_db['traffic_monitor_trip'].delete_many({'trip_id': {'$in': trip_ids}})
        insert_res = self.dynamic_db['failed_trips'].insert_many(docs)
        assert delete_res.deleted_count == len(insert_res.inserted_ids)
        self.update_error_counter += delete_res.deleted_count
        self.trips_rt_errors = []
        # TODO: Logging

    def restore(self):
        """ Restore trips to memory from RealTimeView MongoDB """
        trip_records = self.dynamic_db['traffic_monitor_trip'].find()
        for trip_record in trip_records:

            stops = [StopTime(stop_id=trip_record.get('stop_times')[i].get('stop_id'),
                              stop_name=trip_record.get('stop_times')[i].get('stop_name'),
                              ref_timestamp=trip_record.get('stop_times')[i].get('reference_timestamp'),
                              actual_timestamp=trip_record.get('stop_times')[i].get('actual_timestamp'),
                              # location=trip_record.get('stop_times')[i].get('location'),
                              is_predicted=trip_record.get('stop_times')[i].get('is_predicted'),
                              is_next=trip_record.get('stop_times')[i].get('is_next'))
                     for i in range(len(trip_record.get('stop_times')))]

            trip = Trip(
                trip_id=trip_record.get('trip_id'),
                route_id=trip_record.get('route_id'),
                route_name=trip_record.get('route_name'),
                departure_time=trip_record.get('departure_time'),
                destination=trip_record.get('destination'),
                stop_times=stops,
                location=trip_record.get('location')
            )

            response = self.api_connector.trip_details(trip_id="BKK_" + trip_record.get('trip_id'))
            if response.status_code == 200:
                self.trips.append(trip)
            else:
                print(f"ERROR:\t{response.json().get('text')} [{response.status_code}]")
                self.trips_rt_errors.append(trip)
        # TODO: Logging

    def handle(self, records):
        """ Collect trips to load in RealTimeView MongoDB """
        def handle_error(response, trip_id):
            print(f"ERROR:\t{response.json().get('text')} [{response.status_code}]")
            self.errors.append((trip_id, response.status_code, response.json().get('text')))
            self.trips_actual_errors.append(trip_id)

        def load_trip(response, trip_id, route_id, route_short_name, destination, departure_time):
            trip_details = response.json()
            # print(trip_details.get('data').get('entry'))
            stop_times = trip_details.get('data').get('entry').get('stopTimes')
            if 'vehicle' in trip_details.get('data').get('entry'):
                location = trip_details.get('data').get('entry').get('vehicle').get('location')
            else:
                location = {'lat': None, 'lon': None}
            if 'predictedDepartureTime' not in stop_times[0]:
                # print(f"INFO:\tTrip {trip_id} has no predicted departure time yet.")
                self.queue_counter += 1
                return None
            current_time = trip_details.get('currentTime')
            stop_refs = trip_details.get('data').get('references').get('stops')
            stops = [StopTime(
                stop_id=stop_times[i].get('stopId'),
                stop_name=stop_refs.get(stop_times[i].get('stopId')).get('name'),
                ref_timestamp=stop_times[i].get('arrivalTime') if i > 0 else stop_times[i].get('departureTime'),
                actual_timestamp=stop_times[i].get('predictedArrivalTime') if i > 0 else stop_times[i].get(
                    'predictedDepartureTime'),
                # location={'lat': None, 'lon': None},
                is_predicted=True, is_next=False)
                for i in range(len(stop_times))]
            return Trip(trip_id, route_id, route_short_name, departure_time, destination, stops, location)

        for record in records:
            trip_id = record[2]

            response = self.api_connector.trip_details(trip_id="BKK_" + trip_id)
            if response.status_code != 200:
                handle_error(response, trip_id)
                continue

            route_id = record[0]
            route_name = record[1]
            destination = record[3]
            departure_time = record[4]

            trip = load_trip(response, trip_id, route_id, route_name, destination, departure_time)
            if not trip:
                continue

            self.trips.append(trip)
            self.trips_to_realtime.append(trip)
        # TODO: Logging

    def update(self, records):
        """ Collect trips to update in RealTimeView MongoDB """
        self.trip_ids = [trip.trip_id for trip in records]
        for trip_id in self.trip_ids:
            trip = None
            for t in self.trips:
                if t.trip_id == trip_id:
                    trip = t
                    break
            if not trip:
                print(f"----\nERROR:\ttrip not found with id {trip_id}.\n----")
                continue
            if trip.state == TripState.FINISHED:
                self.save(trip)
                continue
            response = self.api_connector.trip_details(trip_id="BKK_" + trip.trip_id)
            trip_details = response.json()
            if response.status_code != 200:
                print(f"ERROR:\t{trip_details.get('text')} [{response.status_code}]")
                self.errors.append((trip.trip_id, response.status_code, trip_details.get('text')))
                self.trips_rt_errors.append(trip)
                self.trips.remove(trip)
                continue

            stop_times = trip_details.get('data').get('entry').get('stopTimes')

            if 'predictedDepartureTime' not in stop_times[0]:
                self.queue_counter += 1
                # TODO: Logging
                continue

            trip.update(trip_details)
            self.trips_to_update.append(trip)
        # TODO: Logging

    def save(self, trip):
        """ Move finished trips from RealTimeView MongoDB to FinishedTrips MongoDB """
        print(f"INFO:\tTrip {trip.trip_id} has been finished.")
        self.trips_to_save.append(trip)
        # TODO: Logging

    def run(self):
        """ Main process loop with possible restoration at the beginning """
        print(f"INFO:\tProcess started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
        print("INFO:\tRestore trips from database to memory...")
        self.restore()
        print("INFO:\tRestoration done.")
        print("INFO:\tLoading alerts...")
        self.get_alerts()
        print("INFO:\tLoading alerts done.")
        # TODO: Logging
        while True:
            self.insert_counter = 0
            self.update_counter = 0
            self.queue_counter = 0
            self.save_counter = 0
            self.load_error_counter = 0
            self.update_error_counter = 0
            start_time = time()

            if self.refresh_alerts_clock + 60*15 < int(start_time):
                self.get_alerts()

            print("INFO:\tUpdating RealTimeView started...")

            N = int(ceil(len(self.trips) / self.segment_size))
            threads = []
            for n in range(N):
                t = Thread(target=self.update, args=(self.trips[(self.segment_size * n):(self.segment_size * (n + 1))],))
                t.start()
                threads.append(t)
            print(f"INFO:\t{N} threads started.")

            for t in threads:
                t.join()

            print("INFO:\tUpdating RealTimeView finished.")

            # Handle new records arriving from MySQL 'ActualTrips'
            with self.static_db.cursor() as cursor:
                cursor.execute("SELECT * FROM actual_trips;")
                records = cursor.fetchall()
                self.static_db.commit()
            print("INFO:\tLoading new trips into RealTimeView started...")

            print(f"INFO:\tNumber of actual trips need to be processed: {len(records)}")

            N = int(ceil(len(records) / self.segment_size))
            threads = []
            for n in range(N):
                t = Thread(target=self.handle, args=(records[(self.segment_size * n):(self.segment_size * (n + 1))],))
                t.start()
                threads.append(t)
            print(f"INFO:\t{N} threads started.")

            for t in threads:
                t.join()

            print("INFO:\tLoading new trips into RealTimeView finished.")

            print("INFO:\tUpdating databases started...")
            self.execute_db_actual_errors()
            self.execute_db_realtime_errors()
            self.execute_db_update()
            self.execute_db_load()
            self.execute_db_save()
            print("INFO:\tUpdating databases finished.")

            print("--------------------------------------------------------------")
            print(f"INFO:\tProcessing time: {str(round(time() - start_time, 2))}s")
            print(f"INFO:\tAll updates: {str(self.update_counter)}")
            print(f"INFO:\tAll inserts: {str(self.insert_counter)}")
            print(f"INFO:\tAll saves: {str(self.save_counter)}")
            print(f"INFO:\tAll waiting: {str(self.queue_counter)}")
            print(f"INFO:\tAll errors (load): {str(self.load_error_counter)}")
            print(f"INFO:\tAll errors (update): {str(self.update_error_counter)}")
            print("--------------------------------------------------------------")

            sleep(15.0 - ((time() - start_time) % 15.0))
            # TODO: Logging
