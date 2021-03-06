import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
// import { HighchartsChartComponent } from 'highcharts-angular';

import { AppComponent } from './app.component';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {HttpClientModule} from '@angular/common/http';
import { AppRoutingModule } from './app-routing.module';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';
import { TripListComponent } from './components/trip-list/trip-list.component';
import { TripDetailsComponent } from './components/trip-details/trip-details.component';
import {HighchartsChartModule} from 'highcharts-angular';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import {MatTableModule} from '@angular/material/table';
import {MatSortModule} from '@angular/material/sort';
import {MatButtonModule} from '@angular/material/button';
import {MatIconModule} from '@angular/material/icon';
import {MatPaginatorModule} from '@angular/material/paginator';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatInputModule} from '@angular/material/input';
import {MatSelectModule} from '@angular/material/select';
import {MatDividerModule} from '@angular/material/divider';
import { RouteDetailsComponent } from './components/route-details/route-details.component';
import { RouteListComponent } from './components/route-list/route-list.component';
import { LandingComponent } from './components/landing/landing.component';
import {MatCardModule} from "@angular/material/card";
import {DatePipe} from "@angular/common";
import {ScrollingModule} from "@angular/cdk/scrolling";
import { StationListComponent } from './components/station-list/station-list.component';
import { StopDetailsComponent } from './components/stop-details/stop-details.component';
import { BadRequestComponent } from './components/error/bad-request/bad-request.component';
import { ForbiddenComponent } from './components/error/forbidden/forbidden.component';
import { NotFoundComponent } from './components/error/not-found/not-found.component';

@NgModule({
  declarations: [
    AppComponent,
    TripListComponent,
    TripDetailsComponent,
    RouteDetailsComponent,
    RouteListComponent,
    LandingComponent,
    StationListComponent,
    StopDetailsComponent,
    BadRequestComponent,
    ForbiddenComponent,
    NotFoundComponent,
    // HighchartsChartComponent
  ],
  imports: [
    BrowserModule,
    FormsModule,
    HttpClientModule,
    AppRoutingModule,
    NgbModule,
    HighchartsChartModule,
    BrowserAnimationsModule,
    MatTableModule,
    MatSortModule,
    MatButtonModule,
    MatIconModule,
    MatPaginatorModule,
    MatProgressBarModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDividerModule,
    ReactiveFormsModule,
    MatCardModule,
    ScrollingModule
  ],
  providers: [DatePipe],
  bootstrap: [AppComponent]
})
export class AppModule { }
