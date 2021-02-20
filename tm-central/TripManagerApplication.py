import os
from pymongo import MongoClient
import mysql.connector
from services.APIConnector import APIConnector
from controller.TripController import TripController

KEY = os.environ.get('TM_BKK_API_KEY').replace('\'', '')
VERSION = int(os.environ.get('TM_BKK_API_VERSION').replace('\'', ''))
APP_VERSION = os.environ.get('TM_BKK_APP_VERSION').replace('\'', '')

MYSQL_HOST = os.environ.get('TM_MYSQL_HOST').replace('\'', '')
MYSQL_USER = os.environ.get('TM_MYSQL_USER').replace('\'', '')
MYSQL_PASSWORD = os.environ.get('TM_MYSQL_PWD').replace('\'', '')
MYSQL_DATABASE = os.environ.get('TM_MYSQL_DATABASE').replace('\'', '')

MONGO_HOST = os.environ.get('TM_MONGODB_HOST').replace('\'', '')
MONGO_PORT = int(os.environ.get('TM_MONGODB_PORT').replace('\'', ''))
MONGO_DATABASE = os.environ.get('TM_MONGODB_DATABASE').replace('\'', '')

# Init api config
api_connector = APIConnector(KEY, VERSION, APP_VERSION)

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

# Start controller
tripController = TripController(api_connector=api_connector, static_db=static_db, dynamic_db=dynamic_db)
tripController.run()
