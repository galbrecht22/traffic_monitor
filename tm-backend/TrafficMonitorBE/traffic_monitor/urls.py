from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^api/trips$', views.trip_list),
    url(r'^api/trips/(?P<pk>[A-Z0-9]+)$', views.trip_detail),
    url(r'^api/trips/finished$', views.trip_list_finished),
    url(r'^api/routes/(?P<pk>[A-Z0-9]+)$', views.route_travel_times),
    url(r'^api/routes$', views.route_list),
    url(r'^api/stations$', views.station_list),
    url('^api/stations/(?P<pk>[A-Z0-9_]+)$', views.stop_detail),
    url(r'^api/weather$', views.weather),
    url(r'^api/alerts$', views.alerts),
    url(r'^api/list$', views.StationListView.as_view(), name='list'),
]