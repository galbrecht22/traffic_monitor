import { TestBed } from '@angular/core/testing';

import { StopResolver } from './stop.resolver';

describe('StopResolver', () => {
  let resolver: StopResolver;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    resolver = TestBed.inject(StopResolver);
  });

  it('should be created', () => {
    expect(resolver).toBeTruthy();
  });
});
