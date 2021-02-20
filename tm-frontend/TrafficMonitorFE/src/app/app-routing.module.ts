import { NgModule } from '@angular/core';
import {RouterModule, Routes} from '@angular/router';
import {TripListComponent} from './components/trip-list/trip-list.component';
import {TripDetailsComponent} from './components/trip-details/trip-details.component';
import {TripResolver} from './resolvers/trip.resolver';
import {RouteDetailsComponent} from './components/route-details/route-details.component';
import {RouteResolver} from './resolvers/route.resolver';
import {RouteListComponent} from './components/route-list/route-list.component';
import {LandingComponent} from './components/landing/landing.component';

const routes: Routes = [
  { path: '', redirectTo: 'home', pathMatch: 'full' },
  { path: 'trips', component: TripListComponent },
  { path: 'trips/:id', component: TripDetailsComponent, resolve: { trip: TripResolver } },
  { path: 'routes', component: RouteListComponent },
  { path: 'routes/:id', component: RouteDetailsComponent, resolve: {route: RouteResolver} },
  { path: 'home', component: LandingComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
