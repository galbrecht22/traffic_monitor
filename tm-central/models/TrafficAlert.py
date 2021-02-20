from services.APIConnector import APIConnector
import json
from io import StringIO
from html.parser import HTMLParser


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

    def __init__(self, alert_details, alert_route_names):
        self.id = alert_details.get('id')
        self.description = self.strip_tags(alert_details.get('description').get('translations').get('hu'))
        self.header = alert_details.get('header').get('translations').get('hu')
        self.route_ids = alert_details.get('routeIds')
        self.routes = alert_route_names
        self.start = alert_details.get('start')
        self.end = alert_details.get('end')
        self.stop_ids = alert_details.get('stopIds')
        self.url = alert_details.get('url').get('translations').get('hu')

    def __str__(self):
        return json.dumps(self.__dict__, indent=4, ensure_ascii=False)

    def toJSON(self):
        return json.loads(str(self))
