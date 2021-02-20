from django.contrib import admin
from traffic_monitor.models import Trip, StopTime, Route, RouteTrip

# Register your models here.
admin.site.register(Route)
admin.site.register(Trip)
admin.site.register(RouteTrip)
admin.site.register(StopTime)
# admin.site.register(Delay)
