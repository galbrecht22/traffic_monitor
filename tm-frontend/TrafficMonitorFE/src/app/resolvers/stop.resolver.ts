import { Injectable } from '@angular/core';
import {
  Router, Resolve,
  RouterStateSnapshot,
  ActivatedRouteSnapshot
} from '@angular/router';
import { Observable, of } from 'rxjs';
import {StationService} from "../services/station.service";

@Injectable({
  providedIn: 'root'
})
export class StopResolver implements Resolve<any> {
  constructor(private service: StationService) {}
  resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<any>|Promise<any>|any {
    return this.service.get(route.paramMap.get('id'), route.paramMap.get('stop_id'));
  }
}
