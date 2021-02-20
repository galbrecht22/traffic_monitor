import {Component, OnInit, ViewChild, ChangeDetectorRef, AfterViewInit} from '@angular/core';
import {TripService} from '../../services/trip.service';
import {MatTableDataSource} from '@angular/material/table';
import {MatSort} from '@angular/material/sort';
import {MatPaginator} from '@angular/material/paginator';
import {Router} from '@angular/router';
import {FormBuilder, FormControl, Validators} from '@angular/forms';

@Component({
  selector: 'app-trip-list',
  templateUrl: './trip-list.component.html',
  styleUrls: ['./trip-list.component.css']
})
export class TripListComponent implements OnInit, AfterViewInit {

  trips: any;
  displayedColumns: string[] = ['route_name', 'destination', 'departure_time', 'trip_id', 'delay', 'watch'];
  dataSource: MatTableDataSource<any>;
  currentTrip = null;
  currentIndex = -1;
  tripId = '';
  // routes: Set<any> = new Set([]);
  routeDict = {};
  routes = [];
  selectedRoutes = this.routes;

  area = new FormControl('', [Validators.required, ]);
  myForm = this.builder.group({ area: this.area });

  @ViewChild(MatSort) sort: MatSort;
  @ViewChild(MatPaginator, { static: false }) paginator: MatPaginator;

  constructor(private tripService: TripService,
              private router: Router,
              private changeDetectorRefs: ChangeDetectorRef,
              private builder: FormBuilder) { }

  ngAfterViewInit(): void {
        this.changeDetectorRefs.detectChanges();
    }

  ngOnInit(): void {
    this.retrieveTrips();
  }

  retrieveTrips() {
    this.tripService.getAll()
      .subscribe(
        data => {
          this.trips = data;
          this.dataSource = new MatTableDataSource<any>(this.trips);
          this.dataSource.sort = this.sort;
          this.dataSource.paginator = this.paginator;
          this.trips.forEach((element) => {
            this.routeDict[element.route_id] = element.route_name;
            element.delay = Math.max(0,
              element.stop_times[element.next_stop_index].actual_timestamp -
              element.stop_times[element.next_stop_index].reference_timestamp);
            element.delayPercent = Number((100 * Math.min(1, Number((element.delay / 1800)))).toFixed(0));
          });
          Object.keys(this.routeDict).sort().forEach((key) => {
            this.routes.push(this.routeDict[key]);
          });
          console.log(data);
        },
        error => {
          console.log(error);
        });
  }

  setActiveTrip(trip, index) {
    this.currentTrip = trip;
    this.currentIndex = index;
  }

  watchTrip(id) {
    this.router.navigate([`trips/${id}`]);
  }

  updateColor(progress) {
    if (progress < 50) {
      return 'primary';
    }
    else { return 'warn'; }
  }

  applyFilter(event: Event) {
    // console.log(this.dataSource.filter);
    const filterValue = (event.target as HTMLInputElement).value;
    this.dataSource.filter = filterValue.trim().toLowerCase();

    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  submit(filterValue: string) {
    if (!filterValue) {
      this.dataSource.filterPredicate = this.getFilterPredicate(false);
      this.dataSource.filter = '';
      return;
    }
    // this.dataSource.filterPredicate = this.getFilterPredicate(filterValue);
    this.dataSource.filterPredicate = (data: any) => {
      return data.route_name === filterValue;
    };
    this.dataSource.filter = filterValue.trim().toLowerCase();

    if (this.dataSource.paginator) {
      this.dataSource.paginator.firstPage();
    }
  }

  getFilterPredicate(filterValue) {
    if (!filterValue) {
      return (row: any, filter: string) => {
        const matchFilter = [];

        const columnRoute = row.route_name;
        const columnDirection = row.destination;
        const columnTripId = row.trip_id;

        const customFilterRoute = columnRoute.toLowerCase().includes(filter);
        const customFilterDirection = columnDirection.toLowerCase().includes(filter);
        const customFilterTripId = columnTripId.toLowerCase().includes(filter);


        matchFilter.push(customFilterRoute);
        matchFilter.push(customFilterDirection);
        matchFilter.push(customFilterTripId);

        return matchFilter.some(Boolean);
      };
    }
    else {
      return (row: any) => {
        const matchFilter = [];

        const columnRoute = row.route_name;
        const customFilterRoute = columnRoute.toLowerCase().includes(filterValue);

        matchFilter.push(customFilterRoute);

        return matchFilter.every(Boolean);
      };
    }
  }
}
