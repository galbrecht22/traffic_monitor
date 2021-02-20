from djongo import models


class Location(models.Model):
    lat = models.FloatField()
    lon = models.FloatField()

    class Meta:
        abstract = True


# Create your models here.
class StopTime(models.Model):
    stop_id = models.CharField(max_length=70, blank=False, default='', primary_key=True)
    stop_name = models.CharField(max_length=200, blank=False, default='')
    # location = models.EmbeddedField(model_container=Location)
    reference_timestamp = models.IntegerField(blank=False, default=0)
    reference_time = models.CharField(max_length=70, blank=False, default='')
    actual_timestamp = models.IntegerField(blank=False, default=0)
    actual_time = models.CharField(max_length=70, blank=False, default='')
    delay = models.IntegerField(blank=False, default=0)
    is_predicted = models.BooleanField(default=False)
    is_next = models.BooleanField(default=False)


class Trip(models.Model):
    trip_id = models.CharField(max_length=30, blank=False, primary_key=True)
    route_id = models.CharField(max_length=30, blank=False, default='')
    route_name = models.CharField(max_length=70, blank=False, default='')
    departure_time = models.CharField(max_length=70, blank=False, default='')
    destination = models.CharField(max_length=200, blank=False, default='')
    delay = models.IntegerField(blank=False, default=0)
    location = models.EmbeddedField(model_container=Location)
    stop_times = models.ArrayField(model_container=StopTime)
    next_stop_index = models.IntegerField(blank=False, default=0)
    next_stop_name = models.CharField(max_length=200, blank=False, default='')
    state = models.CharField(max_length=10, blank=False, default='')
    latest_update = models.CharField(max_length=70, blank=False, default='')


class RouteTrip(models.Model):
    trip_id = models.CharField(max_length=70, blank=False, primary_key=True)
    destination = models.CharField(max_length=200, blank=False, default='')
    departure_time = models.CharField(max_length=70, blank=False, default='')
    departure_timestamp = models.IntegerField(blank=False, default=0)
    travel_time = models.IntegerField(blank=False, default=0)
    delay = models.IntegerField(blank=False, default=0)


class Route(models.Model):
    route_id = models.CharField(max_length=70, blank=False, primary_key=True)
    route_name = models.CharField(max_length=70, blank=False, default='')
    trips = models.ArrayField(model_container=RouteTrip)
