import {AfterViewInit, ChangeDetectorRef, Component, OnInit, ViewChild} from '@angular/core';
import {WeatherService} from '../../services/weather.service';
import {Router} from '@angular/router';
import {DatePipe, formatDate} from '@angular/common';
import {AlertService} from '../../services/alert.service';
import {MatTableDataSource} from '@angular/material/table';
import {MatSort} from '@angular/material/sort';
import {MatPaginator} from '@angular/material/paginator';

import * as ol from 'ol';
import {Circle, Fill, Stroke, Style} from 'ol/style';
import {Feature, Map, Overlay, View} from 'ol/index';
import {OSM, Vector as VectorSource} from 'ol/source';
import Icon from 'ol/style/Icon';
import * as olProj from 'ol/proj';
import {Tile as TileLayer, Vector as VectorLayer} from 'ol/layer';
import {MultiPoint, Point} from 'ol/geom';
import {useGeographic} from 'ol/proj';
import * as olExtent from 'ol/extent';
import 'ol/ol.css';
import {TripService} from "../../services/trip.service";


@Component({
  selector: 'app-landing',
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss']
})
export class LandingComponent implements OnInit, AfterViewInit {

  weather: any;
  currentDate: any;
  pipe = new DatePipe('en');

  alerts: any;
  routeDict = {};
  routes = [];

  currentAlert: any;

  displayedColumns: string[] = ['description', 'routes'];
  displayedStopColumns: string[] = ['idx', 'name', 'reference_time', 'predicted_reference_time'];
  dataSource: MatTableDataSource<any>;
  stopDataSource: MatTableDataSource<any>;

  trafficMap: any;

  trips: any;

  currentTrip: null;
  currentIndex: -1;

  activeFeature = null;

  @ViewChild(MatSort) sort: MatSort;
  @ViewChild(MatPaginator, { static: false }) paginator: MatPaginator;

  constructor(private weatherService: WeatherService,
              private alertService: AlertService,
              private tripService: TripService,
              private router: Router,
              private changeDetectorRefs: ChangeDetectorRef) {
    // this.currentDate = formatDate(new Date(), 'yyyy/MM/dd', 'en');
    this.currentDate = this.pipe.transform(new Date(), 'medium');
  }

  ngOnInit(): void {
    this.retrieveTrips();
    this.getAlertInfo();
    this.getWeatherInfo();
  }

  ngAfterViewInit(): void {
    this.dataSource = new MatTableDataSource<any>(this.alerts);
    this.dataSource.sort = this.sort;
    this.dataSource.paginator = this.paginator;
    this.changeDetectorRefs.detectChanges();
    console.log(this.dataSource.paginator);
  }

  getWeatherInfo() {
    this.weatherService.get()
      .subscribe(
        data => {
          this.weather = data;
          console.log(data);
        },
        error => {
          console.log(error);
        });
  }

  getAlertInfo() {
    this.alertService.get()
      .subscribe(
        data => {
          this.alerts = data['alerts'];
          for (const alert of this.alerts) {
            for (const route of alert.routes) {
              this.routeDict[route['route_id']] = route['route_name'];
            }
          }
          Object.keys(this.routeDict).sort().forEach((key) => {
            this.routes.push(this.routeDict[key]);
          });
          console.log(this.routes);
          console.log(data);
        },
        error => {
          console.log(error);
        });
  }

  initTrafficMap() {
    useGeographic();
    const place = [19.09417, 47.49961];
    const features = [];
    console.log(this.trips);
    for (const trip of this.trips){
      if (trip.location.lat !== 'None' && trip.location.lon !== 'None') {
        trip.delay = Math.max(0,
          trip.stop_times[trip.next_stop_index].actual_timestamp -
          trip.stop_times[trip.next_stop_index].reference_timestamp);
        let color;
        if (trip.delay < 300) {
          color = 'green';
        }
        else if (trip.delay < 600) {
          color = 'yellow';
        }
        else { color = 'red'; }
        const feature = new Feature({
          geometry: new Point([trip.location.lon, trip.location.lat]),
          color,
          trip,
          originalStyle: null
        });
        features.push(feature);
        // points.push([trip.location.lon, trip.location.lat]);
      }
    }
    const styles = {
      green: new Style({
        image: new Circle({
          radius: 2,
          fill: new Fill({ color: 'green'}),
          stroke: new Stroke({
            width: 1, color: 'green'
          }),
        }),
      }),
      yellow: new Style({
        image: new Circle({
          radius: 3,
          fill: new Fill({ color: 'orange'}),
          stroke: new Stroke({
            width: 2, color: 'orange'
          }),
        }),
      }),
      red: new Style({
        image: new Circle({
          radius: 4,
          fill: new Fill({ color: 'red'}),
          stroke: new Stroke({
            width: 3, color: 'red'
          }),
        }),
      }),
    };

    const vectorSource = new VectorSource({
      features,
      wrapX: false,
    });
    const vector = new VectorLayer({
      source: vectorSource,
      style: feature => styles[feature.get('color')]
    });

    const popup = new Overlay({
      element: null,
      positioning: 'bottom-center',
      stopEvent: false,
      offset: [0, -10],
    });
    this.trafficMap = new Map({
      target: 'traffic_map',
      layers: [
        new TileLayer({
          source: new OSM()
        }),
        vector,
      ],
      view: new View({
        // center: olProj.fromLonLat([19.09417, 47.49961]),
        center: place,
        zoom: 11
      })
    });
    this.trafficMap.addOverlay(popup);
    this.trafficMap.on('click', (event) => {
      const feature = this.trafficMap.getFeaturesAtPixel(event.pixel)[0];
      if (feature) {
        console.log(feature.getProperties().trip);
        this.setActiveTrip(feature.getProperties().trip, 0);
        if (this.activeFeature !== null) {
          this.activeFeature.setStyle(this.activeFeature.orgininalStyle);
          this.activeFeature.changed();
        }
        this.activeFeature = feature;
        this.activeFeature.originalStyle = this.activeFeature.getStyle();
        this.activeFeature.setStyle(new Style({
            image: new Circle({
              radius: 8,
              fill: new Fill({ color: 'black'}),
              stroke: new Stroke({
                width: 6, color: 'white'
              }),
            }),
          }));
        feature.changed();
        //let e = feature.getGeometry().getExtent();
        //let center = olExtent.getCenter(e);
        //this.trafficMap.setView(new ol.View({
        //  center: [center[0], center[1]],
        //  zoom: 11
        //}));
        }
      else {
        if (this.currentTrip) {
          this.currentTrip = null;
          this.currentIndex = -1;
        }
        if (this.activeFeature) {
          this.activeFeature.setStyle(this.activeFeature.originalStyle);
          this.activeFeature.changed();
          this.activeFeature = null;
        }
      }
      // console.log(feature);

    });
  }

  retrieveTrips() {
    this.tripService.getAll()
      .subscribe(
        data => {
          this.trips = data;
          this.initTrafficMap();
          console.log(data);
        },
        error => {
          console.log(error);
        });
  }

  onTrafficMapClick(event) {
    // console.log(event);
  }

  setActiveTrip(trip, index) {
    this.currentTrip = trip;
    this.currentIndex = index;
    this.stopDataSource = new MatTableDataSource<any>(trip.stop_times);
  }

  encodeChar(i: number): string {
    return String.fromCharCode(i);
  }
}
