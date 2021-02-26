from models.TrafficAlert import TrafficAlert
from controller.TripController import TripController
import datetime
from time import sleep, time


class CentralController:
    def __init__(self, api_connector, static_db, dynamic_db):
        self.api_connector = api_connector
        self.static_db = static_db
        self.dynamic_db = dynamic_db
        self.trip_controller = TripController(self.api_connector)
        self.update_counter = 0
        self.insert_counter = 0
        self.save_counter = 0
        self.load_error_counter = 0
        self.update_error_counter = 0
        self.restore_error_counter = 0
        self.thread_segment_size = 100
        self.refresh_alerts_clock = 0

        self.failed = []
        self.nb_restored = 0
        self.finished = []
        self.changed = []
        self.created = []
        self.inner_queued = 0
        self.outer_queued = 0

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

    def execute_update(self):
        """ Update trips in RealTimeView MongoDB """
        if not self.changed:
            return
        for trip in self.changed:
            query = {"trip_id": trip['trip_id']}
            new_values = {"$set": trip}
            update_res = self.dynamic_db['traffic_monitor_trip'].update_one(query, new_values)
            self.update_counter += 1
            # print(update_res.modified_count, trip['trip_id'])
            assert update_res.modified_count == 1
            # maybe matched_count instead of modified_count?
        # TODO: Logging
        self.changed = []

    def execute_load(self):
        """ Move trips from ActualTrips MySQL to RealTimeView MongoDB """
        if not self.created:
            return
        insert_res = self.dynamic_db['traffic_monitor_trip'].insert_many(self.created)
        self.insert_counter += len(insert_res.inserted_ids)

        """ Remove trips from ActualTrips MySQL """
        sql = """DELETE FROM actual_trips WHERE trip_id IN ({})"""
        vals = ["'" + trip['trip_id'] + "'" for trip in self.created]
        with self.static_db.cursor() as cursor:
            cursor.execute(sql.format(','.join(vals)))
            self.static_db.commit()
        self.created = []
        # assert len(insert_res.inserted_ids) == cursor.rowcount

    def execute_save(self):
        """ Move finished trips from RealTimeView MongoDB to FinishedTrips MongoDB """
        if not self.finished:
            return
        trip_ids = [trip['trip_id'] for trip in self.finished]
        insert_res = self.dynamic_db['finished_buffer'].insert_many(self.finished)
        delete_res = self.dynamic_db['traffic_monitor_trip'].delete_many({'trip_id': {'$in': trip_ids}})
        # assert len(insert_res.inserted_ids) == len(delete_res.deleted_count)
        self.save_counter += len(insert_res.inserted_ids)
        self.finished = []
        # TODO: Logging

    def execute_delete(self):
        """ Remove trips with errors from ActualTrips MySQL """
        if not self.failed:
            return
        restore, update, load = [], [], []
        for record in self.failed:
            if record['cause'] == 'restore':
                restore.append(record)
            elif record['cause'] == 'update':
                update.append(record)
            elif record['cause'] == 'load':
                load.append(record)

        if restore:
            delete_res = self.dynamic_db['traffic_monitor_trip'].delete_many({'trip_id': {'$in': restore}})
            self.restore_error_counter += delete_res.deleted_count

        if update:
            delete_res = self.dynamic_db['traffic_monitor_trip'].delete_many({'trip_id': {'$in': update}})
            self.update_error_counter += delete_res.deleted_count

        if load:
            with self.static_db.cursor() as cursor:
                sql = """DELETE FROM actual_trips WHERE trip_id IN ({})"""
                vals = ["'" + trip['trip_id'] + "'" for trip in load]
                cursor.execute(sql.format(','.join(vals)))
                self.static_db.commit()
                self.load_error_counter += cursor.rowcount

        insert_res = self.dynamic_db['failed_trips'].insert_many(self.failed)

        self.failed = []
        # TODO: Logging

    def restore(self):
        """ Restore trips from RealTimeView MongoDB into memory """
        trip_records = list(self.dynamic_db['traffic_monitor_trip'].find())
        nb_success, failures = self.trip_controller.restore(trip_records)
        self.failed.extend(failures)
        self.nb_restored = nb_success
        # TODO: Logging

    def update(self):
        """ Collect trips to update in RealTimeView MongoDB """
        trips, finished, failed, inner_queued = self.trip_controller.update()
        self.changed.extend(trips)
        self.finished.extend(finished)
        self.failed.extend(failed)
        self.inner_queued += inner_queued
        # TODO: Logging

    def load(self, records):
        created, failed, outer_queued = self.trip_controller.load(records)
        self.created.extend(created)
        self.failed.extend(failed)
        self.outer_queued += outer_queued

    def run(self):
        """ Main process loop with possible restoration at the beginning """
        print(f"INFO:\tProcess started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")

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
            self.save_counter = 0
            self.load_error_counter = 0
            self.update_error_counter = 0
            self.restore_error_counter = 0
            self.inner_queued = 0
            self.outer_queued = 0

            start_time = time()

            if self.refresh_alerts_clock + 60*15 < int(start_time):
                print("INFO:\tLoading alerts...")
                self.get_alerts()
                print("INFO:\tLoading alerts finished.")

            print(f"INFO:\tUpdate started...")
            t = time()
            self.update()
            print(f"INFO:\tUpdate finished. Elapsed time: {str(round(time() - t, 2))}s.")

            print("INFO:\tLoading new trips...")
            t = time()
            # Handle new records arriving from MySQL 'ActualTrips'
            with self.static_db.cursor() as cursor:
                cursor.execute("SELECT * FROM actual_trips;")
                records = cursor.fetchall()
                self.static_db.commit()
            print(f"INFO:\tNumber of actual trips need to be processed: {len(records)}")

            self.load(records)
            print(f"INFO:\tLoading new trips finished. Elapsed time: {str(round(time() - t, 2))}s.")

            print("INFO:\tUpdating databases started...")
            t = time()
            self.execute_delete()
            self.execute_save()
            self.execute_update()
            self.execute_load()
            print(f"INFO:\tUpdating databases finished. Elapsed time: {str(round(time() - t, 2))}s.")

            print("----------------------- SUMMARY ------------------------------")
            print(f"INFO:\tFull processing time: {str(round(time() - start_time, 2))}s")
            print(f"INFO:\tAll updates: {str(self.update_counter)}")
            print(f"INFO:\tAll inserts: {str(self.insert_counter)}")
            print(f"INFO:\tAll saves: {str(self.save_counter)}")
            print(f"INFO:\tAll waiting: {str(self.inner_queued + self.outer_queued)}")
            print(f"INFO:\tAll errors (load): {str(self.load_error_counter)}")
            print(f"INFO:\tAll errors (update): {str(self.update_error_counter)}")
            print("-------------------- END OF SUMMARY --------------------------")

            sleep(15.0 - ((time() - start_time) % 15.0))
            # TODO: Logging