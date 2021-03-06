import { NgModule } from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {TripListComponent} from './components/trip-list/trip-list.component';
import {TripDetailsComponent} from './components/trip-details/trip-details.component';
import {TripResolver} from './resolvers/trip.resolver';
import {RouteDetailsComponent} from './components/route-details/route-details.component';
import {RouteResolver} from './resolvers/route.resolver';
import {RouteListComponent} from './components/route-list/route-list.component';
import {LandingComponent} from './components/landing/landing.component';
import {StationListComponent} from "./components/station-list/station-list.component";
import {StopDetailsComponent} from "./components/stop-details/stop-details.component";
import {StopResolver} from "./resolvers/stop.resolver";
import {BadRequestComponent} from "./components/error/bad-request/bad-request.component";
import {ForbiddenComponent} from "./components/error/forbidden/forbidden.component";
import {NotFoundComponent} from "./components/error/not-found/not-found.component";
import {StationListResolver} from "./resolvers/station-list.resolver";

const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'trips', component: TripListComponent },
  { path: 'trips/:id', component: TripDetailsComponent, resolve: { trip: TripResolver } },
  { path: 'routes', component: RouteListComponent },
  { path: 'routes/:id', component: RouteDetailsComponent, resolve: { route: RouteResolver } },
  { path: 'stops', component: StationListComponent },
  { path: 'stops/:id/:stop_id', component: StopDetailsComponent, resolve: { stop: StopResolver } },
  { path: 'home', component: LandingComponent },
  { path: 'error/bad-request', component: BadRequestComponent },
  { path: 'error/forbidden', component: ForbiddenComponent },
  { path: 'error/not-found', component: NotFoundComponent },
  { path: '**', redirectTo: 'home', pathMatch: 'full'},
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
