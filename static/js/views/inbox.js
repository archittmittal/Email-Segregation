/* inbox.js — All emails view with category filter */
const InboxView = {
  _page: 1,
  _total: 0,
  _perPage: 20,
  _category: '',
  _search: '',

  render() {
    return `
      <div class="fade-in">
        <div class="cat-bar" id="cat-bar">
          <button class="cat-pill active-all" data-cat="" onclick="InboxView.filterCat('')">
            <span class="cat-pill-dot" style="background:var(--text-secondary)"></span> All
          </button>
          <button class="cat-pill" data-cat="tonnage" onclick="InboxView.filterCat('tonnage')">
            <span class="cat-pill-dot" style="background:var(--gold)"></span> Tonnage
          </button>
          <button class="cat-pill" data-cat="cargo_vc" onclick="InboxView.filterCat('cargo_vc')">
            <span class="cat-pill-dot" style="background:var(--blue)"></span> Cargo VC
          </button>
          <button class="cat-pill" data-cat="cargo_tc" onclick="InboxView.filterCat('cargo_tc')">
            <span class="cat-pill-dot" style="background:var(--purple)"></span> Cargo TC
          </button>
        </div>

        <div class="table-card">
          <div class="table-toolbar">
            <div class="search-box">
              <span class="search-icon">⌕</span>
              <input type="text" class="search-input" id="inbox-search"
                placeholder="Search emails…" oninput="InboxView.onSearch(this.value)" />
            </div>
            <span class="td-muted" id="inbox-count" style="font-size:13px"></span>
          </div>

          <div class="table-wrapper">
            <table>
              <thead><tr>
                <th>#</th>
                <th>Subject</th>
                <th>Sender</th>
                <th>Category</th>
                <th>Confidence</th>
                <th>Received</th>
                <th>Actions</th>
              </tr></thead>
              <tbody id="inbox-body">
                <tr><td colspan="7"><div class="loading-spinner"><div class="spinner"></div></div></td></tr>
              </tbody>
            </table>
          </div>
          <div class="pagination" id="inbox-pagination"></div>
        </div>
      </div>`;
  },

  async init() {
    this._page = 1;
    this._category = '';
    this._search = '';
    await this.load();
  },

  async load() {
    try {
      const data = await API.emails({
        page: this._page,
        per_page: this._perPage,
        category: this._category,
        search: this._search,
      });
      this._total = data.total;
      this._render(data.emails, data.total);
    } catch (e) {
      Toast.show('Failed to load emails: ' + e.message, 'error');
    }
  },

  _render(emails, total) {
    const start = (this._page - 1) * this._perPage + 1;
    const end   = Math.min(this._page * this._perPage, total);
    document.getElementById('inbox-count').textContent =
      total ? `Showing ${start}–${end} of ${total}` : 'No results';

    const tbody = document.getElementById('inbox-body');
    if (!emails.length) {
      tbody.innerHTML = `<tr><td colspan="7">
        <div class="empty-state">
          <div class="empty-icon">✉</div>
          <div class="empty-text">No emails found</div>
          <div class="empty-sub">Try a different filter or process a new email</div>
        </div></td></tr>`;
    } else {
      tbody.innerHTML = emails.map(e => `
        <tr>
          <td class="td-muted td-mono">#${e.id}</td>
          <td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="${htmlEsc(e.subject||'')}">${htmlEsc(e.subject || 'No Subject')}</td>
          <td class="td-muted" style="font-size:12px">${htmlEsc(e.sender || '—')}</td>
          <td><span class="badge badge-${e.category}">${catLabel(e.category)}</span></td>
          <td><span class="conf-pill">${(e.confidence*100).toFixed(0)}%</span></td>
          <td class="td-muted">${fmtDate(e.created_at)}</td>
          <td>
            <div class="action-cell">
              <button class="btn btn-ghost btn-sm btn-icon-only" title="View raw"
                onclick="InboxView.viewRaw(${e.id})">👁</button>
              <button class="btn btn-danger btn-sm btn-icon-only" title="Delete"
                onclick="InboxView.deleteEmail(${e.id})">🗑</button>
            </div>
          </td>
        </tr>`).join('');
    }

    // Pagination
    const pages = Math.ceil(total / this._perPage);
    const pg = document.getElementById('inbox-pagination');
    if (pages <= 1) { pg.innerHTML = ''; return; }
    pg.innerHTML = `
      <span>${total} total</span>
      <div class="pagination-controls">
        <button class="page-btn" ${this._page<=1?'disabled':''} onclick="InboxView.goPage(${this._page-1})">‹</button>
        ${Array.from({length:Math.min(pages,7)},(_,i)=>{
          const p=i+1;
          return `<button class="page-btn ${p===this._page?'active':''}" onclick="InboxView.goPage(${p})">${p}</button>`;
        }).join('')}
        <button class="page-btn" ${this._page>=pages?'disabled':''} onclick="InboxView.goPage(${this._page+1})">›</button>
      </div>`;
  },

  filterCat(cat) {
    this._category = cat;
    this._page = 1;
    document.querySelectorAll('#cat-bar .cat-pill').forEach(el => {
      el.className = 'cat-pill' + (el.dataset.cat === cat ? ` active-${cat||'all'}` : '');
    });
    this.load();
  },

  onSearch: debounce(function(val) {
    InboxView._search = val;
    InboxView._page = 1;
    InboxView.load();
  }, 350),

  goPage(p) { this._page = p; this.load(); },

  async viewRaw(id) {
    try {
      const email = await API.emailById(id);
      const subject = email.subject || 'No Subject';
      
      let parsedHtml = '';
      if (email.tonnage && email.tonnage.length > 0) {
        parsedHtml += email.tonnage.map(t => `
          <div class="parsed-record-card tonnage">
            <div class="parsed-record-title">🚢 Vessel: ${htmlEsc(t.vessel_name)}</div>
            <div class="parsed-field-grid">
              <div class="parsed-field"><label>Size</label><span class="mono">${htmlEsc(t.vessel_size || '—')}</span></div>
              <div class="parsed-field"><label>Open Port</label><span>${htmlEsc(t.open_port || '—')}</span></div>
              <div class="parsed-field"><label>Open Date</label><span>${htmlEsc(t.open_date || '—')}</span></div>
              <div class="parsed-field"><label>Type</label><span>${htmlEsc(t.vessel_type || '—')}</span></div>
              <div class="parsed-field"><label>Flag</label><span>${htmlEsc(t.flag || '—')}</span></div>
              <div class="parsed-field"><label>Built</label><span class="mono">${htmlEsc(t.built_year || '—')}</span></div>
            </div>
          </div>`).join('');
      }
      if (email.cargo_vc && email.cargo_vc.length > 0) {
        parsedHtml += email.cargo_vc.map(c => `
          <div class="parsed-record-card cargo_vc">
            <div class="parsed-record-title">📦 Voyage Cargo: ${htmlEsc(c.cargo_name || 'Bulk Cargo')}</div>
            <div class="parsed-field-grid">
              <div class="parsed-field"><label>Quantity</label><span class="mono">${htmlEsc(c.quantity || '—')}</span></div>
              <div class="parsed-field"><label>Load Port</label><span>${htmlEsc(c.loading_port || '—')}</span></div>
              <div class="parsed-field"><label>Disch Port</label><span>${htmlEsc(c.discharge_port || '—')}</span></div>
              <div class="parsed-field"><label>Laycan</label><span>${htmlEsc(c.laycan || '—')}</span></div>
              <div class="parsed-field"><label>Type</label><span>${htmlEsc(c.cargo_type || '—')}</span></div>
            </div>
          </div>`).join('');
      }
      if (email.cargo_tc && email.cargo_tc.length > 0) {
        parsedHtml += email.cargo_tc.map(c => `
          <div class="parsed-record-card cargo_tc">
            <div class="parsed-record-title">⏱ Time Charter: ${htmlEsc(c.cargo_name || 'TCT Requirement')}</div>
            <div class="parsed-field-grid">
              <div class="parsed-field"><label>Delivery</label><span>${htmlEsc(c.delivery_port || '—')}</span></div>
              <div class="parsed-field"><label>Redelivery</label><span>${htmlEsc(c.redelivery_port || '—')}</span></div>
              <div class="parsed-field"><label>Duration</label><span class="mono">${htmlEsc(c.duration || '—')}</span></div>
              <div class="parsed-field"><label>Laycan</label><span>${htmlEsc(c.laycan || '—')}</span></div>
              <div class="parsed-field"><label>Type</label><span>${htmlEsc(c.cargo_type || '—')}</span></div>
            </div>
          </div>`).join('');
      }
      if (!parsedHtml) {
        parsedHtml = `
          <div class="empty-state" style="padding: 24px 0">
            <div class="empty-icon">📭</div>
            <div class="empty-text" style="font-size:13px">No records extracted</div>
            <div class="empty-sub">This email was classified but no fields were matched by regex.</div>
          </div>`;
      }

      // If this email is a duplicate, add info about the original email it duplicated
      let dupInfoHtml = '';
      if (email.is_duplicate) {
        dupInfoHtml = `
          <div class="duplicate-warning" style="margin: 0 0 16px 0; display: block;">
            ⚠ Duplicate of previous email.
          </div>`;
      }

      const modal = document.createElement('div');
      modal.className = 'modal-overlay open';
      modal.innerHTML = `
        <div class="modal" style="max-width:960px">
          <div class="modal-header">
            <h2 class="modal-title" style="font-size:15px">${htmlEsc(subject)}</h2>
            <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
          </div>
          <div class="modal-body" style="padding: 20px 24px;">
            <div style="margin-bottom:16px;display:flex;gap:10px;align-items:center;flex-wrap:wrap">
              <span class="badge badge-${email.category}">${catLabel(email.category)}</span>
              <span class="conf-pill">${(email.confidence*100).toFixed(0)}% confidence</span>
              <span class="td-muted" style="font-size:12px">From: ${htmlEsc(email.sender||'')}</span>
            </div>
            ${dupInfoHtml}
            <div class="modal-split">
              <div class="modal-split-left">
                <div class="modal-split-header">Raw Email Body</div>
                <pre class="modal-raw-body-pre">${htmlEsc(email.raw_body||'')}</pre>
              </div>
              <div class="modal-split-right">
                <div class="modal-split-header">Extracted Structured Data</div>
                <div class="modal-parsed-panel">${parsedHtml}</div>
              </div>
            </div>
          </div>
        </div>`;
      modal.onclick = e => { if (e.target === modal) modal.remove(); };
      document.body.appendChild(modal);
    } catch (e) {
      Toast.show('Error loading email: ' + e.message, 'error');
    }
  },

  async deleteEmail(id) {
    if (!confirm('Delete this email and all its extracted data?')) return;
    try {
      await API.deleteEmail(id);
      Toast.show('Email deleted', 'success');
      this.load();
    } catch (e) {
      Toast.show('Delete failed: ' + e.message, 'error');
    }
  },
};

window.viewEmailSource = function(id) {
  InboxView.viewRaw(id);
};
