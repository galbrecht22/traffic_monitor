import os
import json
import requests
from math import floor
from datetime import datetime, timedelta, date
from time import time

from io import StringIO
from html.parser import HTMLParser

from django.db.models import QuerySet, Avg
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter, OrderingFilter

from traffic_monitor.models import Trip, Route, Stop, Station
from traffic_monitor.serializers import TripSerializer, RouteTripSerializer, RouteSerializer, StopSerializer, \
    StationSerializer

from bson import ObjectId

from pymongo import MongoClient

client = MongoClient(
    'mongodb://localhost:27017')

todays_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
tomorrows_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
tomorrows_day = tomorrows_date.day + 1
tomorrows_date.replace(day=tomorrows_day)


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


class TrafficAlert:
    @staticmethod
    def strip_tags(html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()

    def __init__(self, alert_details):
        print(alert_details)
        self.id = alert_details.get('id')
        self.description = self.strip_tags(alert_details.get('description').get('translations').get('hu'))
        self.header = alert_details.get('header').get('translations').get('hu')
        self.route_ids = alert_details.get('routeIds')
        self.start = alert_details.get('start')
        self.end = alert_details.get('end')
        self.stop_ids = alert_details.get('stopIds')
        self.url = alert_details.get('url').get('translations').get('hu')

    def __str__(self):
        return json.dumps(self.__dict__, indent=4, ensure_ascii=False)

    def toJSON(self):
        return json.loads(str(self))


class OWMConnector:
    def __init__(self, base_url: str, key: str, city: str = "Budapest", units: str = "metric", lang: str = "hu"):
        self.base_url = base_url
        self.key = key
        self.city = city
        self.units = units
        self.lang = lang

    def get_weather_info(self, **kwargs):
        request_url = f"{self.base_url}?appid={self.key}&q={self.city}&units={self.units}&lang={self.lang}"
        if kwargs:
            params = ''.join('&' + k + '=' + v for k, v in kwargs.items() if v)
            request_url += params
        print(request_url)
        response = requests.get(request_url)
        return response


class OWMEntity:
    def __init__(self, raw_details):
        self.description = raw_details['weather'][0]['description']
        self.temperature = raw_details['main']['temp']
        self.humidity = raw_details['main']['humidity']
        self.wind_speed = raw_details['wind']['speed']
        self.icon = raw_details['weather'][0]['icon']

    def __str__(self):
        return json.dumps(self.__dict__, indent=4, ensure_ascii=False)

    def toJSON(self):
        return json.loads(str(self))


@api_view(['GET'])
def trip_list(request):
    if request.method == 'GET':
        trips = Trip.objects.all()

        trip_id = request.GET.get('trip_id', None)
        if trip_id is not None:
            trips = trips.filter(trip_id__icontains=trip_id)

        trips_serializer = TripSerializer(trips, many=True)
        for i in trips_serializer.data:
            # print(i)
            i['location'] = json.loads(i['location'])
            if i['location']['lat'] != 'None':
                i['location']['lat'] = float(i['location']['lat'])
            if i['location']['lon'] != 'None':
                i['location']['lon'] = float(i['location']['lon'])
        return JsonResponse(trips_serializer.data, safe=False, json_dumps_params={'indent': 2, 'ensure_ascii': False})
        # 'safe=False' for objects serialization


@api_view(['GET'])
def trip_detail(request, pk):
    if request.method == 'GET':

        try:
            trip = Trip.objects.get(pk=pk)
        except Trip.DoesNotExist:
            print('In Exception...')
            trip = client['traffic_monitor']['finished_buffer'].find_one({
                'trip_id': pk}, {"_id": 0})
            if trip:
                return JsonResponse(trip, json_dumps_params={'indent': 2, 'ensure_ascii': False})
            else:
                print('Not found in buffer')
                trip = client['traffic_monitor']['finished_trips'].find_one({
                    'trip_id': pk, "departure_time": {"$gte": todays_date, "$lt": tomorrows_date}}, {"_id": 0})
                if trip:
                    return JsonResponse(trip, json_dumps_params={'indent': 2, 'ensure_ascii': False})
                else:
                    print('Not found in finished')
                    trip = client['traffic_monitor']['failed_trips'].find_one({
                        "snapshot": {"$exists": True}, "snapshot.trip_id": pk,
                        "time": {"$gte": todays_date, "$lt": tomorrows_date}
                    }, {"_id": 0})
                    if trip:
                        return JsonResponse(trip, json_dumps_params={'indent': 2, 'ensure_ascii': False})
                    else:
                        print('Not Found anywhere.')
                        return JsonResponse({'message': 'The trip does not exist'},
                                            status=status.HTTP_404_NOT_FOUND,
                                            json_dumps_params={'indent': 2, 'ensure_ascii': False})

        trip_serializer = TripSerializer(trip)
        return JsonResponse(trip_serializer.data, json_dumps_params={'indent': 2, 'ensure_ascii': False})


@api_view(['GET'])
def trip_list_finished(request):
    # GET all finished trips...
    trips = Trip.objects.filter(state="Finished")

    if request.method == 'GET':
        trips_serializer = TripSerializer(trips, many=True)
        return JsonResponse(trips_serializer.data, safe=False, json_dumps_params={'indent': 2, 'ensure_ascii': False})


def get_route_pipeline(pk, interval):
    with open('traffic_monitor/route_details.json') as f:
        pipeline = json.load(f)
    pipeline[1]['$match']['route_id'] = pk
    pipeline[0]['$addFields']['trips']['$map']['in']['timeBucket']['$mod'][0]['$multiply'][0]['$floor']['$divide'][
        1] = interval * 60
    pipeline[0]['$addFields']['trips']['$map']['in']['timeBucket']['$mod'][0]['$multiply'][1] = interval * 60

    return pipeline


@api_view(['GET'])
def route_travel_times(request, pk):
    interval = 30
    i = request.GET.get('interval', None)
    if i:
        interval = int(i)
    result = client['traffic_monitor']['traffic_monitor_route'].aggregate(pipeline=get_route_pipeline(pk, interval))

    res = [doc for doc in result]
    route_name = res[0]['route_name']
    r = {'route_id': pk, 'route_name': route_name, 'result': res}
    return JsonResponse(r, json_dumps_params={'indent': 2, 'ensure_ascii': False})


@api_view(['GET'])
def route_list(request):
    if request.method == 'GET':
        routes = Route.objects.all()

        route_id = request.GET.get('route_id', None)
        if route_id is not None:
            routes = routes.filter(route_id__icontains=route_id)

        routes_serializer = RouteSerializer(routes, many=True)
        return JsonResponse(routes_serializer.data, safe=False, json_dumps_params={'indent': 2, 'ensure_ascii': False})
        # 'safe=False' for objects serialization


@api_view(['GET'])
def weather(request):
    if request.method == 'GET':
        api_key = os.environ.get('TM_OWM_API_KEY').replace('\'', '')

        # base_url variable to store url
        base_url = "http://api.openweathermap.org/data/2.5/weather"

        owm_connector = OWMConnector(base_url=base_url, key=api_key, city='Budapest')
        response = owm_connector.get_weather_info()
        response_json = response.json()
        if response.status_code != 200:
            print(f"Error: {response_json['message']}")
            return JsonResponse(response_json,
                                status=response.status_code,
                                json_dumps_params={'indent': 2, 'ensure_ascii': False})
        else:
            current_weather = OWMEntity(response.json())
            return JsonResponse(current_weather.toJSON(), json_dumps_params={'indent': 2, 'ensure_ascii': False})


@api_view(['GET'])
def alerts(request):
    if request.method == 'GET':
        result = client['traffic_monitor']['traffic_alerts'].find({})
        res = [doc for doc in result]
        r = {'alerts': res}
        return JsonResponse(json.loads(JSONEncoder().encode(r)), json_dumps_params={'indent': 2, 'ensure_ascii': False})


def json_dt_patch(o):
    import datetime
    if isinstance(o, date) or isinstance(o, datetime):
        return o.strftime("%Y/%m/%d %H:%M:%S")
    return o


@api_view(['GET'])
def station_list(request):
    if request.method == 'GET':
        # t = time()
        # stations = Station.objects.all()
        # print(f"station.objects.all(): {round(time() - t, 2)}s")
        #
        # t = time()
        # stations_serializer = StationSerializer(stations, many=True)
        # print(f"StationSerializer(stations, many=True): {round(time() - t, 2)}s")
        #
        # t = time()
        # # print(stations_serializer.data)
        # jsonResponse = JsonResponse(stations_serializer.data, safe=False,
        #                             json_dumps_params={'indent': 2, 'ensure_ascii': False})
        # print(f"JsonResponse(stations_serializer.data, safe=False): {round(time() - t, 2)}s")
        # return jsonResponse

        # t = time()
        with open('traffic_monitor/station_list.json') as f:
            pipeline = json.load(f)
        # print(f"load: {time() - t}s")

        # t = time()
        result = client['traffic_monitor']['traffic_monitor_station'].aggregate(pipeline=pipeline)
        # print(f"client: {time() - t}s")

        # t = time()
        res = [doc for doc in result]
        # print(f"result: {time() - t}s")

        r = {'stations': res}
        # print(len(res))

        t = time()
        # jsonResponse = JsonResponse(json.loads(json.dumps(r, default=json_dt_patch)),
        #                             json_dumps_params={'indent': 2, 'ensure_ascii': False}, safe=False)
        jsonResponse = Response(r)
        print(f"Building JsonResponse: {time() - t}s")
        return jsonResponse


@api_view(['GET'])
def stop_detail(request, pk):
    if request.method == 'GET':
        stop_pk = request.GET.get('stop_id', None)
        if not stop_pk:
            return JsonResponse({'message': 'No stop specified'},
                                status=status.HTTP_404_NOT_FOUND,
                                json_dumps_params={'indent': 2, 'ensure_ascii': False})
        try:
            station = Station.objects.get(pk=pk)
        except Station.DoesNotExist:
            return JsonResponse({'message': 'The station does not exist'},
                                status=status.HTTP_404_NOT_FOUND,
                                json_dumps_params={'indent': 2, 'ensure_ascii': False})

        stop = next((stop for stop in station.stops if stop['stop_id'] == stop_pk), None)
        if not stop:
            return JsonResponse({'message': 'The stop does not exist'},
                                status=status.HTTP_404_NOT_FOUND,
                                json_dumps_params={'indent': 2, 'ensure_ascii': False})

        stop_serializer = StopSerializer(stop)
        return JsonResponse(stop_serializer.data, json_dumps_params={'indent': 2, 'ensure_ascii': False})


class StationListView(ListAPIView):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    pagination_class = PageNumberPagination
    filter_backends = (SearchFilter, OrderingFilter)
    search_fields = ('station_id', 'station_name', 'maxDelta', 'avgDelta')
