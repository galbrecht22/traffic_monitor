import mysql.connector
import os
from pymongo import MongoClient


MYSQL_HOST = os.environ.get('TM_MYSQL_HOST').replace('\'', '')
MYSQL_USER = os.environ.get('TM_MYSQL_USER').replace('\'', '')
MYSQL_PASSWORD = os.environ.get('TM_MYSQL_PWD').replace('\'', '')
MYSQL_DATABASE = os.environ.get('TM_MYSQL_DATABASE').replace('\'', '')

MONGO_HOST = os.environ.get('TM_MONGODB_HOST').replace('\'', '')
MONGO_PORT = int(os.environ.get('TM_MONGODB_PORT').replace('\'', ''))
MONGO_DATABASE = os.environ.get('TM_MONGODB_DATABASE').replace('\'', '')

# Init static DB config
static_db = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE
)

# Init dynamic DB config
client = MongoClient(MONGO_HOST, MONGO_PORT)
dynamic_db = client[MONGO_DATABASE]


tables_dict = {
    'daily_trips':  1,
    'actual_trips': 1
}

collection_dict = {
    'finished_trips':          0,
    'finished_buffer':         1,
    'failed_trips':            0,
    'traffic_monitor_route':   0,
    'traffic_monitor_station': 0,
    'traffic_monitor_trip':    1
}
truncate_stations = 1

tables_to_clean = [k for k, v in tables_dict.items() if v]
collections_to_clean = [k for k, v in collection_dict.items() if v]

sql = "DELETE FROM {};"

with static_db.cursor() as cursor:
    for table in tables_to_clean:
        print(f"Executing DELETE FROM {table}...",)
        cursor.execute(sql.format(table))
        print("Done.")
    static_db.commit()

static_db.close()

for collection in collections_to_clean:
    print(f"Executing {collection}.delete_many()...",)
    dynamic_db[collection].delete_many({})
    print("Done.")

if truncate_stations:
    dynamic_db['traffic_monitor_station'].update_many({}, {"$set": {"stops.$[].trips": []}})
    dynamic_db['traffic_monitor_station'].update_many({}, {"$set": {"stops.$[].current_delays": []}})
    dynamic_db['traffic_monitor_station'].update_many({}, {"$set": {"stops.$[].maxDelta": 0}})
    dynamic_db['traffic_monitor_station'].update_many({}, {"$set": {"stops.$[].avgDelta": 0}})
    dynamic_db['traffic_monitor_station'].update_many({}, {"$set": {"maxDelta": 0}})
    dynamic_db['traffic_monitor_station'].update_many({}, {"$set": {"avgDelta": 0}})

client.close()
