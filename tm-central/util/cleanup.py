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


tables_to_clean = [
    'daily_trips',
    'actual_trips'
]

sql = "DELETE FROM {};"

with static_db.cursor() as cursor:
    for table in tables_to_clean:
        print(f"Executing DELETE FROM {table}...",)
        cursor.execute(sql.format(table))
        print("Done.")
    static_db.commit()

static_db.close()

collections_to_clean = [
    # 'finished_trips',
    'finished_buffer',
    # 'failed_trips',
    # 'trip_details',
    # 'traffic_monitor_route',
    'traffic_monitor_trip'
]

for collection in collections_to_clean:
    print(f"Executing {collection}.delete_many()...",)
    dynamic_db[collection].delete_many({})
    print("Done.")

client.close()
