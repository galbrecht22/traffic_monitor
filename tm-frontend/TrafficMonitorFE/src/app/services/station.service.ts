import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";

const baseUrl = 'http://localhost:8080/api/stations';

@Injectable({
  providedIn: 'root'
})
export class StationService {

  constructor(private http: HttpClient) { }

  get(stationId, stopId) {
    return this.http.get(`${baseUrl}/${stationId}?stop_id=${stopId}`);
  }
  getAll() {
    return this.http.get(baseUrl);
  }
}
