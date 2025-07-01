import { ComponentFixture, TestBed } from '@angular/core/testing';

import { WorkflowsListComponent } from './workflows-list.component';

describe('WorkflowsListComponent', () => {
  let component: WorkflowsListComponent;
  let fixture: ComponentFixture<WorkflowsListComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [WorkflowsListComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(WorkflowsListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
