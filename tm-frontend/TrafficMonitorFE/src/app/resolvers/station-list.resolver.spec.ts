import { TestBed } from '@angular/core/testing';

import { StationListResolver } from './station-list.resolver';

describe('StationListResolver', () => {
  let resolver: StationListResolver;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    resolver = TestBed.inject(StationListResolver);
  });

  it('should be created', () => {
    expect(resolver).toBeTruthy();
  });
});
