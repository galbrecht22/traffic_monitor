import {
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  OnInit,
  TemplateRef,
  ViewChild,
  ViewContainerRef
} from '@angular/core';
import * as Highcharts from 'highcharts';
import {StationService} from "../../services/station.service";
import {ActivatedRoute, Router} from "@angular/router";

@Component({
  selector: 'app-stop-details',
  templateUrl: './stop-details.component.html',
  styleUrls: ['./stop-details.component.css']
})
export class StopDetailsComponent implements OnInit, AfterViewInit {

  currentStop = null;
  activeTrip = null;
  highcharts = Highcharts;
  data = [];
  currentDate = new Date();

  @ViewChild('outlet', { read: ViewContainerRef }) outletRef: ViewContainerRef;
  @ViewChild('content', { read: TemplateRef }) contentRef: TemplateRef<any>;

  chartOptions = {
    chart: {
      type: 'scatter',
      animation: false
    },
    title: {
      text: 'Delay deltas of the trips during time'
    },
    xAxis: {
      minorTickInterval: 'auto',
      startOnTick: true,
      endOnTick: true,
      type: 'datetime',
      dateTimeLabelFormats: {
        year: '%H:%M:%S',
        month: '%H:%M:%S',
        day: '%H:%M:%S',
        hour: '%H:%M:%S',
        minute: '%H:%M:%S',
        second: '%H:%M:%S'
      },
      min: this.currentDate.valueOf(),
      gridLineWidth: 3,
      minorGridLineWidth: 1,
      gridLineColor: '#d8d8d8',
      minorGridLineColor: '#d8d8d8',
    },
    yAxis: {
      title: {
        text: 'Delay Delta (min)'
      },
      type: 'linear',
      min: 0,
      minRange: 4
    },
    tooltip: {
      pointFormat: 'trip: <b>{point.trip.route_name}</b><br/>delay_delta: <b>{point.y}</b><br/>',
      valueSuffix: ' min',
    },
    plotOptions: {
      series: {
        cursor: 'pointer',
        point: {
          events: {
            click: (event) => {
              console.log(event.point.trip);
              this.router.navigate([`trips/${event.point.trip.trip_id}`],
                { queryParams: { stop: event.point.stopId}})
                .catch(err => {
                switch (err.status) {
                  case 400:
                    this.router.navigate(['error', 'bad-request']);
                    break;
                  case 403:
                    this.router.navigate(['error', 'forbidden']);
                    break;
                  case 404:
                    this.router.navigate(['error', 'not-found']);
                    break;
                  default:
                    this.router.navigate(['error', 'not-found']);
              }});
            }
          }
        }
      }
    },
    series: this.data
  };

  constructor(
    private stationService: StationService,
    private route: ActivatedRoute,
    private router: Router,
    private changeDetectorRefs: ChangeDetectorRef) { }


  ngOnInit(): void {
    this.route.queryParams.subscribe(params => {
      console.log(params.valueOf());
      if (params !== {}) {
        this.activeTrip = params.trip;
      }
    });
    this.route.data.subscribe(data => {
      this.currentStop = data.stop;
    }, error => {
      console.log(error);
    });
    this.currentDate.setUTCHours(4, 0, 0, 0);
    this.chartOptions.xAxis.min = this.currentDate.valueOf();
    this.getChartData();
  }

  ngAfterViewInit(): void {
    this.outletRef.createEmbeddedView(this.contentRef);
    this.changeDetectorRefs.detectChanges();
  }

  private rerender() {
    this.outletRef.clear();
    this.outletRef.createEmbeddedView(this.contentRef);
  }

  // async getStop(id): Promise<any> {
  //   this.stationService.get(id).subscribe(data => {
  //     this.currentStop = data;
  //     this.getChartData();
  //   }, error => {
  //     console.log(error);
  //   });
  // }

  getChartData() {
    console.log(this.currentStop);
    this.data = [];
    this.data.push({
      name: 'stop', data: [], animation: false
    });
    this.currentStop.trips.forEach(element => {
      this.data[0].data.push({x: new Date(element.arrival_time),
        y: Number((element.delay_delta / 60).toFixed(1)),
        trip: element, color: '#00A0E3', fillColor: '#00A0E3', stopId: this.currentStop.stop_id});
    });
    if (this.activeTrip !== null) {
      console.log(this.data[0].data);
      for (const element of this.data[0].data) {
        if (element.trip.trip_id === this.activeTrip) {
          element.color = '#ff0000';
          // element.fillColor = '#ff0000';
          element.marker = { symbol: 'triangle', radius: 6, fillColor: '#ff0000'};
          break;
        }
      }
    }
    this.chartOptions.series = this.data;
    console.log(this.data);
  }

}
