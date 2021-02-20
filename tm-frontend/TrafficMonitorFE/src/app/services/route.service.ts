import { Injectable } from '@angular/core';
import {HttpClient} from '@angular/common/http';

const baseUrl = 'http://localhost:8080/api/routes';

@Injectable({
  providedIn: 'root'
})
export class RouteService {

  constructor(private http: HttpClient) { }

  get(id, interval) {
    return this.http.get(`${baseUrl}/${id}?interval=${interval}`);
  }

  getAll() {
    return this.http.get(baseUrl);
  }
}
