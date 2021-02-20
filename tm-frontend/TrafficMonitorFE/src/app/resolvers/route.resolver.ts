import { Injectable } from '@angular/core';
import {
  Router, Resolve,
  RouterStateSnapshot,
  ActivatedRouteSnapshot
} from '@angular/router';
import { Observable, of } from 'rxjs';
import {RouteService} from '../services/route.service';


@Injectable({
  providedIn: 'root'
})
export class RouteResolver implements Resolve<any> {

  constructor(private service: RouteService) { }
  resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<any>|Promise<any>|any {
    return this.service.get(route.paramMap.get('id'), 30);
  }
}
