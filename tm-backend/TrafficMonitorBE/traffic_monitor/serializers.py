from rest_framework import serializers
from .models import Trip, StopTime, RouteTrip, Route, Stop, Station, StopTrip


class StopTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StopTime
        fields = ('stop_id', 'stop_name', 'station_id',
                  'reference_timestamp', 'actual_timestamp',
                  'reference_time', 'actual_time', 'delay',
                  'delay_delta', 'is_predicted', 'is_next')
        abstract = True


class TripSerializer(StopTimeSerializer):
    stop_times = StopTimeSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = ('trip_id', 'route_id', 'route_name', 'departure_time',
                  'destination', 'delay', 'location', 'stop_times',
                  'next_stop_index', 'next_stop_name', 'state', 'latest_update')


class RouteTripSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteTrip
        fields = ('trip_id', 'destination',
                  'departure_time', 'departure_timestamp',
                  'travel_time', 'delay')
        abstract = True


class RouteSerializer(RouteTripSerializer):
    trips = RouteTripSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ('route_id', 'route_name', 'trips')


class StopTripSerializer(serializers.ModelSerializer):
    class Meta:
        model = StopTrip
        fields = ('trip_id', 'route_id', 'route_name',
                  'arrival_time', 'destination',
                  'delay', 'delay_delta')
        abstract = True


class StopSerializer(StopTripSerializer):
    trips = StopTripSerializer(many=True, read_only=True)
    current_delays = serializers.JSONField()

    class Meta:
        model = Stop
        fields = ('stop_id', 'stop_name', 'station_id', 'maxDelta', 'avgDelta', 'trips', 'current_delays')
        abstract = True


class StationSerializer(StopSerializer):
    stops = StopSerializer(many=True, read_only=True)

    class Meta:
        model = Station
        fields = ('station_id', 'station_name', 'maxDelta', 'avgDelta', 'stops')
