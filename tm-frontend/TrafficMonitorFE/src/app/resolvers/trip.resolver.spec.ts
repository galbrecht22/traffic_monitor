import { TestBed } from '@angular/core/testing';

import { TripResolver } from './trip.resolver';

describe('TripResolver', () => {
  let resolver: TripResolver;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    resolver = TestBed.inject(TripResolver);
  });

  it('should be created', () => {
    expect(resolver).toBeTruthy();
  });
});
