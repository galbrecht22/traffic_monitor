import { Injectable } from '@angular/core';
import {
  Router, Resolve,
  RouterStateSnapshot,
  ActivatedRouteSnapshot
} from '@angular/router';
import { Observable, of } from 'rxjs';
import {TripService} from '../services/trip.service';

@Injectable({
  providedIn: 'root'
})
export class TripResolver implements Resolve<any> {

  constructor(private service: TripService) {}

  resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<any>|Promise<any>|any {
    return this.service.get(route.paramMap.get('id'));
  }
}
