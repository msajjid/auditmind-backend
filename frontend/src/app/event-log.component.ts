import { CommonModule } from '@angular/common';
import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';

import { Evidence } from './models';

@Component({
  selector: 'app-event-log',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="card table-card">
      <div class="section-header">
        <div>
          <p class="eyebrow">Evidence log</p>
          <h3>Outputs</h3>
        </div>
        <div class="event-log-tools">
          <input
            class="input"
            type="search"
            placeholder="Search title, controls, or source"
            [value]="searchTerm"
            (input)="setSearch($any($event.target).value)"
          />
          <span class="chip">{{ filteredEvidence.length }} records</span>
        </div>
      </div>
      <div *ngIf="loading" class="subdued">Loading evidence…</div>
      <div class="table-wrapper">
        <table class="table" *ngIf="pagedEvidence.length; else emptyTable">
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Controls</th>
              <th>Confidence</th>
              <th>Updated</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr *ngFor="let ev of pagedEvidence; trackBy: trackEvidenceById">
              <td>
                <div class="table-title">{{ displayTitleFn(ev) }}</div>
                <div class="subdued">{{ ev.source_type_id || 'source unknown' }}</div>
              </td>
              <td>
                <span class="badge-success" *ngIf="ev.ai_classification">Classified</span>
                <span class="badge-warn" *ngIf="!ev.ai_classification">Pending</span>
              </td>
              <td>
                <div class="tags" *ngIf="primaryControlsFn(ev).length; else noControls">
                  <span class="tag" *ngFor="let ctrl of primaryControlsFn(ev)">{{ ctrl }}</span>
                </div>
                <ng-template #noControls><span class="subdued">—</span></ng-template>
              </td>
              <td>{{ ev.ai_classification?.confidence ? (ev.ai_classification?.confidence | percent: '1.0-1') : '—' }}</td>
              <td>{{ ev.updated_at ? (ev.updated_at | date: 'short') : '—' }}</td>
              <td class="detail-cell">
                <button class="btn-ghost info-btn" type="button" (click)="openDetail(ev)">Details</button>
              </td>
            </tr>
          </tbody>
        </table>
        <ng-template #emptyTable>
          <p class="subdued">No evidence yet.</p>
        </ng-template>
      </div>
      <div class="pagination-row" *ngIf="totalPages > 1">
        <button class="btn-ghost" type="button" (click)="goPage('prev')" [disabled]="page === 0">Prev</button>
        <span class="page-pill">{{ page + 1 }} / {{ totalPages }}</span>
        <button class="btn-ghost" type="button" (click)="goPage('next')" [disabled]="page + 1 >= totalPages">Next</button>
      </div>

      <div class="detail-backdrop" *ngIf="selectedEvidence">
        <div class="detail-modal card">
          <div class="modal-header">
            <div>
              <p class="eyebrow">Evidence detail</p>
              <h3>{{ displayTitleFn(selectedEvidence) }}</h3>
              <p class="subdued">Source: {{ selectedEvidence.source_type_id || 'unknown' }}</p>
            </div>
            <button class="btn-ghost" type="button" (click)="closeDetail()">Close</button>
          </div>

          <div class="detail-grid">
            <div class="detail-card">
              <h4>Record</h4>
              <div class="kv">
                <span class="key">Evidence ID</span>
                <span class="value monospace">{{ selectedEvidence.id }}</span>
              </div>
              <div class="kv">
                <span class="key">Organization</span>
                <span class="value monospace">{{ selectedEvidence.organization_id }}</span>
              </div>
              <div class="kv">
                <span class="key">Status</span>
                <span class="value">{{ selectedEvidence.status || '—' }}</span>
              </div>
              <div class="kv">
                <span class="key">Created</span>
                <span class="value">{{ formatDate(selectedEvidence.created_at) }}</span>
              </div>
              <div class="kv">
                <span class="key">Updated</span>
                <span class="value">{{ formatDate(selectedEvidence.updated_at) }}</span>
              </div>
            </div>

            <div class="detail-card">
              <h4>Classification</h4>
              <div class="kv">
                <span class="key">Confidence</span>
                <span class="value">{{ selectedEvidence.ai_classification?.confidence ? (selectedEvidence.ai_classification?.confidence | percent: '1.0-1') : '—' }}</span>
              </div>
              <div class="kv" *ngIf="selectedEvidence.ai_classification?.pipeline_run_id">
                <span class="key">Pipeline run</span>
                <span class="value monospace">{{ selectedEvidence.ai_classification?.pipeline_run_id }}</span>
              </div>
              <div class="kv" *ngIf="selectedEvidence.ai_classification?.agent_run_id">
                <span class="key">Agent run</span>
                <span class="value monospace">{{ selectedEvidence.ai_classification?.agent_run_id }}</span>
              </div>
              <div class="kv" *ngIf="selectedEvidence.ai_classification?.cache_hit">
                <span class="key">Cache hit</span>
                <span class="value">Yes</span>
              </div>
              <div class="kv" *ngIf="selectedEvidence.ai_classification?.similarity">
                <span class="key">Similarity</span>
                <span class="value">{{ selectedEvidence.ai_classification?.similarity | number: '1.2-2' }}</span>
              </div>
              <div class="kv" *ngIf="selectedEvidence.ai_classification?.created_tasks?.length">
                <span class="key">Created tasks</span>
                <span class="value">{{ selectedEvidence.ai_classification?.created_tasks?.join(', ') }}</span>
              </div>
              <div class="kv" *ngIf="primaryControlsFn(selectedEvidence).length">
                <span class="key">Primary controls</span>
                <span class="value tags">
                  <span class="tag" *ngFor="let ctrl of primaryControlsFn(selectedEvidence)">{{ ctrl }}</span>
                </span>
              </div>
            </div>

            <div class="detail-card wide">
              <h4>Raw classification</h4>
              <pre class="raw">{{ stringify(selectedEvidence.ai_classification) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      .event-log-tools {
        display: flex;
        align-items: center;
        gap: 10px;
        width: 100%;
        justify-content: flex-end;
      }
      .event-log-tools .input {
        max-width: 280px;
      }
      .pagination-row {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-top: 12px;
      }
      .page-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 6px 10px;
        border-radius: 999px;
        border: 1px solid var(--border);
        color: var(--muted);
        background: rgba(255, 255, 255, 0.04);
        font-size: 12px;
      }
      .detail-cell {
        text-align: right;
      }
      .info-btn {
        padding: 8px 10px;
      }
      .detail-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.55);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 18px;
        z-index: 30;
      }
      .detail-modal {
        width: min(1100px, 100%);
        max-height: 92vh;
        overflow: auto;
        display: grid;
        gap: 16px;
      }
      .detail-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 12px;
      }
      .detail-card {
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 12px;
        background: rgba(255, 255, 255, 0.02);
      }
      .detail-card.wide {
        grid-column: 1 / -1;
      }
      .kv {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        padding: 6px 0;
        border-bottom: 1px dashed var(--border);
      }
      .kv:last-child {
        border-bottom: none;
      }
      .kv .key {
        color: var(--muted);
        font-size: 12px;
      }
      .kv .value {
        text-align: right;
        font-weight: 600;
      }
      .monospace {
        font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
      }
      .raw {
        background: rgba(0, 0, 0, 0.2);
        padding: 12px;
        border-radius: 12px;
        border: 1px solid var(--border);
        overflow: auto;
        max-height: 300px;
        white-space: pre-wrap;
        word-break: break-word;
      }
    `,
  ],
})
export class EventLogComponent implements OnChanges {
  @Input() evidenceList: Evidence[] = [];
  @Input() displayTitleFn: (evidence: Evidence) => string = (ev) => ev.title || 'Evidence';
  @Input() primaryControlsFn: (evidence: Evidence) => string[] = () => [];
  @Input() loading = false;

  searchTerm = '';
  page = 0;
  readonly pageSize = 8;
  selectedEvidence: Evidence | null = null;

  ngOnChanges(_: SimpleChanges): void {
    this.page = Math.min(this.page, Math.max(this.totalPages - 1, 0));
  }

  trackEvidenceById(_: number, item: Evidence): string {
    return item.id;
  }

  setSearch(term: string): void {
    this.searchTerm = term || '';
    this.page = 0;
  }

  get filteredEvidence(): Evidence[] {
    const term = this.searchTerm.trim().toLowerCase();
    if (!term) return [...this.evidenceList];
    return this.evidenceList.filter((ev) => {
      const haystack = [
        this.displayTitleFn(ev),
        ev.source_type_id || '',
        (ev.description as string) || '',
        this.primaryControlsFn(ev).join(' '),
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(term);
    });
  }

  get totalPages(): number {
    if (!this.filteredEvidence.length) return 0;
    return Math.ceil(this.filteredEvidence.length / this.pageSize);
  }

  get pagedEvidence(): Evidence[] {
    if (!this.filteredEvidence.length) return [];
    const start = this.page * this.pageSize;
    return this.filteredEvidence.slice(start, start + this.pageSize);
  }

  goPage(direction: 'prev' | 'next'): void {
    const total = this.totalPages;
    if (!total) return;
    if (direction === 'prev') {
      this.page = Math.max(0, this.page - 1);
    } else {
      this.page = Math.min(total - 1, this.page + 1);
    }
  }

  openDetail(ev: Evidence): void {
    this.selectedEvidence = ev;
  }

  closeDetail(): void {
    this.selectedEvidence = null;
  }

  formatDate(value?: string): string {
    if (!value) return '—';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return '—';
    return parsed.toLocaleString();
  }

  stringify(obj: unknown): string {
    if (!obj) return '—';
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return '—';
    }
  }
}
