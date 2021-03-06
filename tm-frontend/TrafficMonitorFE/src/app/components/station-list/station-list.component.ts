import {AfterViewInit, ChangeDetectorRef, Component, OnInit, ViewChild} from '@angular/core';
import {MatTableDataSource} from '@angular/material/table';
import {MatSort} from '@angular/material/sort';
import {MatPaginator} from '@angular/material/paginator';
import {ActivatedRoute, Router} from '@angular/router';
import {StationService} from '../../services/station.service';

@Component({
  selector: 'app-station-list',
  templateUrl: './station-list.component.html',
  styleUrls: ['./station-list.component.scss']
})
export class StationListComponent implements OnInit, AfterViewInit {

  stations: any;
  currentStation = null;
  currentIndex = -1;
  stops: any;
  displayedColumns: string[] = ['station_id', 'station_name', 'stops', 'maxDelta', 'watch'];
  displayedStopColumns: string[] = ['stop_id', 'stop_name', 'routes', 'health', 'watchStop'];
  dataSource: MatTableDataSource<any> = new MatTableDataSource<any>();
  stopDataSource: MatTableDataSource<any> = new MatTableDataSource<any>();

  @ViewChild(MatSort) sort: MatSort;
  @ViewChild(MatPaginator, { static: false }) paginator: MatPaginator;

  constructor(private stationService: StationService,
              private router: Router,
              private route: ActivatedRoute,
              private changeDetectorRefs: ChangeDetectorRef) { }

  ngOnInit(): void {
    this.retrieveStations();
  }

  ngAfterViewInit(): void {
    this.changeDetectorRefs.detectChanges();
  }

  calculateAvgDelta(station) {
      let avgDelta = 0;
      for (let i = 0; i < Math.min(4, station.stops.length); i++) {
        avgDelta += station.stops[i].avgDelta;
      }
      if (station.stops.length > 0) {
        avgDelta /= Math.min(4, station.stops.length);
      }
      station.avgDelta = Number((avgDelta / 60).toFixed(0));
  }

  calculateMaxDelta(station) {
    let maxDelta = 0;
    station.stops.forEach(stop => {
      maxDelta = stop.maxDelta > maxDelta ? stop.maxDelta : maxDelta;
    });
    station.maxDelta = Number((maxDelta / 60).toFixed(0));
  }

  sortStopsByAvgDelta() {
    return (a, b) => {
      if (a.avgDelta === b.avgDelta) {
        return 0;
      }
      else if (a.avgDelta === undefined || a.avgDelta === null) {
        return 1;
      }
      else if (b.avgDelta === undefined || b.avgDelta === null) {
        return -1;
      }
      else {
        return a.avgDelta < b.avgDelta ? 1 : -1;
      }
    };

  }

  retrieveStations() {
    this.stationService.getAll().subscribe(data => {
      this.stations = data['stations'];
      this.stations.forEach(station => {
        station.stops.sort(this.sortStopsByAvgDelta());
        this.calculateAvgDelta(station);
        this.calculateMaxDelta(station);
      });
      this.dataSource.data = this.stations;
      this.dataSource.sort = this.sort;
      this.dataSource.sortingDataAccessor = (station, property) => {
        switch (property) {
          case 'stops': {
            return station.avgDelta;
          }
          case 'maxDelta': {
            return station.maxDelta;
          }
          default: {
            return station[property];
          }
        }
      };
      this.dataSource.paginator = this.paginator;
      console.log(this.stations);
    }, error => {
      console.log(error);
    });
  }

  watchStation(station) {
    console.log(station);
    this.setActiveStation(station, 0);
  }

  setActiveStation(station, index) {
    this.currentStation = station;
    this.currentIndex = index;
    this.stopDataSource.data = station.stops;
  }

  watchStop(stop) {
    console.log(stop);
    // this.setActiveStop(stop, 0);
    this.router.navigate([`stops/${this.currentStation.station_id}/${stop.stop_id}`]);
  }

  setActiveStop(stop, index) {
    // this.router.navigate([`stops/${stop.stop_id}`]);
  }

  getBgForStop(stop) {
    // return '#00A0E3';
    if (stop.trips.length === 0 || stop.avgDelta === undefined) {
      // console.log('Empty');
      // return '#00A0E3';
      return '#ffffff';
    }

    const percentColors = [
      { pct: 0.0, color: { r: 0x00, g: 0xff, b: 0 }},
      { pct: 0.5, color: { r: 0xff, g: 0xff, b: 0 }},
      { pct: 1.0, color: { r: 0xff, g: 0x00, b: 0 }}
    ];
    const rate = Math.min(1.0, stop.avgDelta / 120.0);
    if (isNaN(rate)) {
      // console.log(stop.trips);
      return '#ffffff';
    }
    for (var i = 1; i < percentColors.length - 1; i++) {
      if (rate < percentColors[i].pct) {
        break;
      }
    }
    const lower = percentColors[i - 1];
    const upper = percentColors[i];
    const range = upper.pct - lower.pct;
    const rangePct = (rate - lower.pct) / range;
    const pctLower = 1 - rangePct;
    const pctUpper = rangePct;
    const color = {
      r: Math.floor(lower.color.r * pctLower + upper.color.r * pctUpper),
      g: Math.floor(lower.color.g * pctLower + upper.color.g * pctUpper),
      b: Math.floor(lower.color.b * pctLower + upper.color.b * pctUpper)
      };
    // console.log(rate);
    return 'rgb(' + [color.r, color.g, color.b].join(',') + ')';
  }

  getRoutes(stop) {
    const routes = new Set();
    stop.trips.forEach(trip => {
      routes.add(trip.route_name);
    });
    return routes;
  }
}
