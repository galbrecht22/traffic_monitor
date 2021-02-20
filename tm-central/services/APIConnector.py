import requests
import json


class APIConnector:
    def __init__(self, key: str, version: int, app_version: str):
        self.url = "https://futar.bkk.hu/api/query/v1/ws/otp/api/where/"
        self.key = key
        self.version = version
        self.app_version = app_version

    @staticmethod
    def jprint(obj):
        text = json.dumps(obj, sort_keys=True, indent=4, ensure_ascii=False)
        print(text)

    @staticmethod
    def underscore_to_camelCase(s):
        res = s.split('_')
        return "".join([res[0]] + [part.title() for part in res[1:]])

    def create_request(self, name, *args, **kwargs):
        const_params = [self.underscore_to_camelCase(str(k)) + "=" + str(v) for k, v in self.__dict__.items() if k != "url"]
        req = self.url + str(name.replace("_", "-") + ".json?") + "&".join(const_params + [
            self.underscore_to_camelCase(str(k)) + "=" + str(v) for k, v in kwargs.items() if v
        ])
        return req

    def validate_references(self, include_references):
        if not include_references:
            return
        else:
            if type(include_references) != list:
                raise TypeError("Invalid type of references.")
            return ",".join(include_references)

    def metadata(self, include_references=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.metadata.__name__, include_references=references)

        res = requests.get(req_str)
        return res

    def bicycle_rental(self, include_references=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.bicycle_rental.__name__, include_references=references)

        res = requests.get(req_str)
        return res

    def alert_search(self, include_references=None, query=None, start=None, end=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.alert_search.__name__,
                                      include_references=references,
                                      query=query,
                                      start=start,
                                      end=end)
        res = requests.get(req_str)
        return res

    def search(self, query, include_references=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.search.__name__,
                                      include_references=references,
                                      query=query)
        res = requests.get(req_str)

        return res

    def stops_for_location(self, lon, lat, lon_span=None, lat_span=None, radius=None, query=None, include_references=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.stops_for_location.__name__,
                                      lon=lon, lat=lat,
                                      lon_span=lon_span, lat_span=lat_span,
                                      radius=radius,
                                      include_references=references,
                                      query=query)
        res = requests.get(req_str)
        return res

    def arrivals_and_departures_for_stop(self, stop_id, include_references=None, only_departures=None, limit=None,
                                          minutes_before=None, minutes_after=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.arrivals_and_departures_for_stop.__name__,
                                      stop_id=stop_id,
                                      include_references=references,
                                      only_departures=only_departures,
                                      limit=limit,
                                      minutes_before=minutes_before,
                                      minutes_after=minutes_after)
        res = requests.get(req_str)
        return res

    def arrivals_and_departures_for_location(self, lon, lat, client_lon, client_lat, lon_span=None, lat_span=None,
                                              radius=None, only_departures=None, limit=None, group_limit=None,
                                              include_references=None, minutes_before=None, minutes_after=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.arrivals_and_departures_for_location.__name__,
                                      lon=lon, lat=lat,
                                      client_lon=client_lon, client_lat=client_lat,
                                      lon_span=lon_span, lat_span=lat_span,
                                      radius=radius,
                                      group_limit=group_limit,
                                      include_references=references,
                                      only_departures=only_departures,
                                      limit=limit,
                                      minutes_before=minutes_before,
                                      minutes_after=minutes_after)
        res = requests.get(req_str)
        return res

    def schedule_for_stop(self, stop_id, include_references=None, only_departures=None, date=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.schedule_for_stop.__name__,
                                      stop_id=stop_id,
                                      include_references=references,
                                      only_departures=only_departures,
                                      date=date)
        res = requests.get(req_str)
        return res

    def route_details(self, route_id, include_references=None, related=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.route_details.__name__,
                                      route_id=route_id,
                                      include_references=references,
                                      related=related)
        res = requests.get(req_str)
        return res

    def trip_details(self, trip_id, vehicle_id=None, include_references=None, date=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.trip_details.__name__,
                                      trip_id=trip_id,
                                      vehicle_id=vehicle_id,
                                      include_references=references,
                                      date=date)
        res = requests.get(req_str)
        return res

    def vehicles_for_location(self, lon, lat, lon_span=None, lat_span=None, include_references=None,
                              radius=None, query=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.vehicles_for_location.__name__,
                                      lon=lon, lat=lat,
                                      lon_span=lon_span, lat_span=lat_span,
                                      radius=radius,
                                      query=query,
                                      include_references=references)
        res = requests.get(req_str)
        return res

    def vehicles_for_route(self, route_id, related=None, include_references=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.vehicles_for_route.__name__,
                                      route_id=route_id,
                                      include_references=references,
                                      related=related)
        res = requests.get(req_str)
        return res

    def vehicles_for_stop(self, stop_id, include_references=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.vehicles_for_stop.__name__,
                                      stop_id=stop_id,
                                      include_references=references)
        res = requests.get(req_str)
        return res

    def plan_trip(self, from_place, to_place, date=None, time=None, include_references=None):
        references = self.validate_references(include_references)
        req_str = self.create_request(self.plan_trip.__name__,
                                      from_place=from_place,
                                      to_place=to_place,
                                      date=date,
                                      time=time,
                                      include_references=references)
        res = requests.get(req_str)
        return res
