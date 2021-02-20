import os
from pymongo import MongoClient
from time import sleep, time
from datetime import datetime

MONGO_HOST = os.environ.get('TM_MONGODB_HOST').replace('\'', '')
MONGO_PORT = int(os.environ.get('TM_MONGODB_PORT').replace('\'', ''))
MONGO_DATABASE = os.environ.get('TM_MONGODB_DATABASE').replace('\'', '')

# Init dynamic DB config
client = MongoClient(MONGO_HOST, MONGO_PORT)
dynamic_db = client[MONGO_DATABASE]

while True:
    start_time = time()
    x = dynamic_db['finished_buffer'].find()
    print(f"{dynamic_db['finished_buffer'].count_documents({})} trips to process...")

    ids = []
    records = []
    for t in x:
        ids.append(t['trip_id'])
        records.append(t)
        result = {}
        result['route_id'] = t['route_id']
        result['route_name'] = t['route_name']
        trip = {}
        trip['trip_id'] = t['trip_id']
        trip['destination'] = t['destination']
        trip['departure_time'] = t['departure_time']
        trip['departure_timestamp'] = datetime.timestamp(datetime.strptime(t['departure_time'], '%Y-%m-%d %H:%M:%S'))
        trip['travel_time'] = t['stop_times'][-1]['actual_timestamp'] - \
                              t['stop_times'][0]['actual_timestamp']
        trip['delay'] = max(0,
                            t['stop_times'][-1]['actual_timestamp'] -
                            t['stop_times'][-1]['reference_timestamp'])
        # trip['delay'] = sum(t['stop_times'][i]['actual_timestamp'] -
        #                     t['stop_times'][i]['reference_timestamp']
        #                     for i in range(len(t['stop_times']))) / len(t['stop_times'])
        # print(trip['travel_time'])
        present = dynamic_db['traffic_monitor_route'].find_one({'route_id': result['route_id']})
        # print(present)
        if not present:
            result['trips'] = [trip]
            inserted = dynamic_db['traffic_monitor_route'].insert_one(result)
        else:
            res = dynamic_db['traffic_monitor_route'].update_one({'route_id': result['route_id']}, {'$push': {'trips': trip}})

    deleted = dynamic_db['finished_buffer'].delete_many({'trip_id': {'$in': ids}})
    if records:
        y = dynamic_db['finished_trips'].insert_many(records)
    print("--------------------------------------------------------------")
    print(f"INFO:\tProcessing time: {str(round(time() - start_time, 2))}s")
    print(f"INFO:\t{deleted.deleted_count} trips processed successfully.")
    print("--------------------------------------------------------------")
    sleep(15.0 - ((time() - start_time) % 15.0))
