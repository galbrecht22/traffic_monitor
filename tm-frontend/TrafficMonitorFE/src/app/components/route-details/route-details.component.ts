import {
  AfterContentInit,
  AfterViewInit,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  TemplateRef,
  ViewChild,
  ViewContainerRef
} from '@angular/core';
import {TripService} from '../../services/trip.service';
import {ActivatedRoute} from '@angular/router';
import {RouteService} from '../../services/route.service';
import * as Highcharts from 'highcharts';


@Component({
  selector: 'app-route-details',
  templateUrl: './route-details.component.html',
  styleUrls: ['./route-details.component.css']
})
export class RouteDetailsComponent implements OnInit, AfterViewInit, AfterContentInit, OnDestroy {
  currentRoute: any;
  currentId: string;
  currentRouteName: string;
  interval = null;
  highcharts = Highcharts;
  frequency = 30;
  data = [
    {name: 'Travel time', type: 'column', animation: true, yAxis: 0, data: []},
    {name: 'Delay', type: 'spline', animation: true, yAxis: 1, data: []}
    ];
  @ViewChild('outlet', {read: ViewContainerRef}) outletRef: ViewContainerRef;
  @ViewChild('content', {read: TemplateRef}) contentRef: TemplateRef<any>;

  chartOptions = {
    chart: {
      type: 'column',
      animation: true
    },
    title: {
      text: 'Change of journey time across a day'
    },
    xAxis: [{
      categories: [],
      type: 'datetime',
      dateTimeLabelFormats: {
        year: '%M:%S',
        month: '%M:%S',
        day: '%M:%S',
        hour: '%M:%S',
        minute: '%M:%S',
        second: '%M:%S'
      },
    }],
    yAxis: [{
      gridLineWidth: 0,
      title: {
        text: 'Journey time (minutes)'
      },
      type: 'datetime',
      dateTimeLabelFormats: {
        year: '%H:%M:%S',
        month: '%H:%M:%S',
        day: '%H:%M:%S',
        hour: '%H:%M:%S',
        minute: '%H:%M:%S',
        second: '%H:%M:%S'
      },
      min: 3500000,
      opposite: true
    }, {
      // tickInterval: 60000,
        gridLineWidth: 0,
        title: {
          text: 'Delay (minutes)'
        },
        type: 'datetime',
        dateTimeLabelFormats: {
          year: '%H:%M:%S',
          month: '%H:%M:%S',
          day: '%H:%M:%S',
          hour: '%H:%M:%S',
          minute: '%H:%M:%S',
          second: '%H:%M:%S'
        },
        min: 0,
        max: 1000000
      }],
    tooltip: {
      shared: true,
      valueSuffix: ' ms',
    },
    series: this.data
  };


  constructor(private routeService: RouteService,
              private route: ActivatedRoute,
              private changeDetectorRefs: ChangeDetectorRef) { }

  ngAfterViewInit(): void {
    this.outletRef.createEmbeddedView(this.contentRef);
    this.changeDetectorRefs.detectChanges();
    }

  ngOnInit(): void {
    this.route.data.subscribe(data => {
        this.currentRoute = data.route.result;
        this.currentId = data.route.route_id;
        this.currentRouteName = data.route.route_name;
        console.log(data);
      },
      error => {
        console.log(error);
      });
    this.getChartData();
    // this.interval = setInterval(() => {
    //   this.refreshData(this.currentId).then(data => {
    //     this.rerender();
    //   });
    // }, 5000);
  }

  private rerender() {
    this.outletRef.clear();
    this.outletRef.createEmbeddedView(this.contentRef);
  }

  async refreshData(id): Promise<any> {
    return this.getRoute(id);
  }

  async getRoute(id): Promise<any> {
    this.routeService.get(id, this.frequency)
      .subscribe(
        data => {
          this.currentRoute = data;
          this.currentId = this.currentRoute.route_id;
          this.currentRouteName = this.currentRoute.route_name;
          this.currentRoute = this.currentRoute.result;
          console.log(this.currentRoute);
          this.getChartData();
          this.rerender();
          console.log(data);
        },
        error => {
          console.log(error);
        });
  }

  getChartData() {
    console.log(this.currentRoute);
    this.chartOptions.xAxis[0].categories = [];
    this.data[0].data = [];
    this.data[1].data = [];
    console.log(this.currentRoute);
    this.currentRoute.forEach( (element) => {
      const date = new Date(parseInt(element.timeBucket) * 1000);
      const hours = date.getHours();
      const minutes = '0' + date.getMinutes();
      this.chartOptions.xAxis[0].categories.push(hours + ':' + minutes.substr(-2));
      this.data[0].data.push(Math.max(0, (element.avgTravel) * 1000));
      this.data[1].data.push(Math.max(0, (element.avgDelay) * 1000));
    });
    this.chartOptions.yAxis[0].min = Math.min(...this.data[0].data) * 0.95;
    this.chartOptions.yAxis[0].max = Math.max(...this.data[0].data) * 1.05;
    this.chartOptions.yAxis[1].min = 0;
    this.chartOptions.yAxis[1].max = Math.max(...this.data[1].data) * 1.25;
    this.chartOptions.series = this.data;
    console.log(this.data);
    console.log(this.chartOptions);
  }

  ngAfterContentInit(): void {
    this.changeDetectorRefs.detectChanges();
  }

  ngOnDestroy(): void {
    if (this.interval) {
      clearInterval(this.interval);
    }
  }

  changeInterval(interval): void {
    this.frequency = interval;
    this.refreshData(this.currentId).then(data => {
      console.log('rerender');
      this.rerender();
      console.log('rerendered');
      });

  }

}
