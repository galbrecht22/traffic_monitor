import {Component, OnInit, ViewChild, ChangeDetectorRef, AfterViewInit} from '@angular/core';
import {RouteService} from '../../services/route.service';
import {MatTableDataSource} from '@angular/material/table';
import {MatSort} from '@angular/material/sort';
import {MatPaginator} from '@angular/material/paginator';
import {Router} from '@angular/router';
import {FormBuilder, FormControl, Validators} from '@angular/forms';

@Component({
  selector: 'app-route-list',
  templateUrl: './route-list.component.html',
  styleUrls: ['./route-list.component.css']
})
export class RouteListComponent implements OnInit, AfterViewInit {

  routes: any;
  displayedColumns: string[] = ['route', 'route_id', 'watch'];
  dataSource: MatTableDataSource<any>;
  currentRoute = null;
  currentIndex = -1;

  @ViewChild(MatSort) sort: MatSort;
  @ViewChild(MatPaginator, { static: false }) paginator: MatPaginator;

  constructor(private routeService: RouteService,
              private router: Router,
              private changeDetectorRefs: ChangeDetectorRef) { }

  ngAfterViewInit(): void {
    this.changeDetectorRefs.detectChanges();
  }

  ngOnInit(): void {
    this.retrieveRoutes();
  }

  retrieveRoutes() {
    this.routeService.getAll()
      .subscribe(
        data => {
          this.routes = data;
          this.dataSource = new MatTableDataSource<any>(this.routes);
          this.dataSource.sort = this.sort;
          this.dataSource.paginator = this.paginator;
          console.log(data);
        },
        error => {
          console.log(error);
        });
  }

  setActiveRoute(route, index) {
    this.currentRoute = route;
    this.currentIndex = index;
  }

  watchRoute(id) {
    this.router.navigate([`routes/${id}`]);
  }
}
