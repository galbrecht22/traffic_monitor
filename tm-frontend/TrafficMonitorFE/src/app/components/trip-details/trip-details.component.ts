import {
  AfterContentInit,
  AfterViewInit,
  ChangeDetectorRef,
  Component, OnDestroy,
  OnInit,
  TemplateRef,
  ViewChild,
  ViewContainerRef
} from '@angular/core';
import {TripService} from '../../services/trip.service';
import {ActivatedRoute, Router} from '@angular/router';
import * as Highcharts from 'highcharts';
import DateTimeFormat = Intl.DateTimeFormat;

@Component({
  selector: 'app-trip-details',
  templateUrl: './trip-details.component.html',
  styleUrls: ['./trip-details.component.css']
})
export class TripDetailsComponent implements OnInit, AfterViewInit, AfterContentInit, OnDestroy {

  currentTrip = null;
  message = '';
  highcharts = Highcharts;
  data = [];
  interval = null;
  @ViewChild('outlet', {read: ViewContainerRef}) outletRef: ViewContainerRef;
  @ViewChild('content', {read: TemplateRef}) contentRef: TemplateRef<any>;

  chartOptions = {
    chart: {
      type: 'spline',
      animation: false
    },
    title: {
      text: 'Current delay at the stations'
    },
    xAxis: {
      categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    },
    yAxis: {
      title: {
        text: 'Latency (minutes)'
      },
      type: 'datetime',
      dateTimeLabelFormats: {
        year: '%M:%S',
        month: '%M:%S',
        day: '%M:%S',
        hour: '%M:%S',
        minute: '%M:%S',
        second: '%M:%S'
      },
      min: 0,
    },
    tooltip: {
      valueSuffix: ' ms',
    },
    series: this.data
  };


  constructor(
    private tripService: TripService,
    private route: ActivatedRoute,
    private router: Router,
    private changeDetectorRefs: ChangeDetectorRef) { }

  ngOnInit(): void {
    this.route.data.subscribe(data => {
        this.currentTrip = data.trip;
        console.log(data);
      },
      error => {
        console.log(error);
      });
    this.message = '';
    this.getChartData();
    this.interval = setInterval(() => {
      this.refreshData(this.currentTrip.trip_id).then(data => {
        this.rerender();
      });
    }, 5000);
  }

  async refreshData(id): Promise<any> {
    // this.route_name.data.subscribe(data => {
    //     this.currentTrip = data.trip;
    //     console.log(data);
    //   },
    //   error => {
    //     console.log(error);
    //   });
    // this.message = '';
    // this.getChartData();
    return this.getTrip(id);
  }

  ngAfterViewInit(): void {
    this.outletRef.createEmbeddedView(this.contentRef);
    this.changeDetectorRefs.detectChanges();
  }

  ngAfterContentInit(): void {
  }

  private rerender() {
    this.outletRef.clear();
    this.outletRef.createEmbeddedView(this.contentRef);
  }

  async getTrip(id): Promise<any> {
    this.tripService.get(id)
      .subscribe(
        data => {
          this.currentTrip = data;
          this.getChartData();
          console.log(data);
        },
        error => {
          console.log(error);
        });
  }

  deleteTrip() {
    this.tripService.delete(this.currentTrip.id)
      .subscribe(
        response => {
          console.log(response);
          this.router.navigate(['/trips']);
        },
        error => {
          console.log(error);
        });
  }

  getChartData() {
    console.log(this.currentTrip);
    this.chartOptions.xAxis.categories = [];
    this.data = [];
    this.data.push({
      name: 'trip', data: [], animation: false, zoneAxis: 'x', zones: [
        { value: Math.max(this.currentTrip.next_stop_index, 0), color: '#000', fillColor: '#000', dashStyle: 'Solid' },
        { color: '#dddddd', fillColor: '#dddddd', dashStyle: 'Dash' },
      ]
    });
    console.log(this.currentTrip);
    this.currentTrip.stop_times.forEach( (element) => {
      this.chartOptions.xAxis.categories.push(element.stop_name);
      this.data[0].data.push(Math.max(0, (element.actual_timestamp - element.reference_timestamp) * 1000));
    });
    this.data[0].data[this.currentTrip.next_stop_index] = {
      y: this.data[0].data[this.currentTrip.next_stop_index],
      color: 'red',
      marker: { /* symbol: 'circle', */ radius: 8, fillColor: 'red' }
    };
    this.chartOptions.series = this.data;
    console.log(this.data);
    console.log(this.chartOptions);
  }

  ngOnDestroy(): void {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }
}
