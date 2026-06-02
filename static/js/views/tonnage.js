/* tonnage.js — Tonnage vessel records view */
const TonnageView = {
  _page: 1, _total: 0, _perPage: 20, _search: '',

  render() {
    return `
      <div class="fade-in">
        <div class="table-card">
          <div class="table-toolbar">
            <div class="search-box">
              <span class="search-icon">⌕</span>
              <input type="text" class="search-input" id="tonnage-search"
                placeholder="Search vessel or port…" oninput="TonnageView.onSearch(this.value)" />
            </div>
            <div style="display:flex;gap:8px;align-items:center">
              <span class="td-muted" id="tonnage-count" style="font-size:13px"></span>
              <button class="btn btn-ghost btn-sm" onclick="API.exportTonnage()" title="Export to CSV">⬇ Export CSV</button>
            </div>
          </div>
          <div class="table-wrapper">
            <table>
              <thead><tr>
                <th>Vessel Name</th>
                <th>DWT / Size</th>
                <th>Open Port</th>
                <th>Open Date</th>
                <th>Flag</th>
                <th>Built</th>
                <th>Type</th>
                <th>Account</th>
                <th>Actions</th>
              </tr></thead>
              <tbody id="tonnage-body">
                <tr><td colspan="9"><div class="loading-spinner"><div class="spinner"></div></div></td></tr>
              </tbody>
            </table>
          </div>
          <div class="pagination" id="tonnage-pagination"></div>
        </div>
      </div>`;
  },

  async init() { this._page = 1; this._search = ''; await this.load(); },

  async load() {
    try {
      const data = await API.tonnage({ page: this._page, per_page: this._perPage, search: this._search });
      this._total = data.total;
      this._render(data.records, data.total);
    } catch (e) { Toast.show('Failed to load tonnage: ' + e.message, 'error'); }
  },

  _render(records, total) {
    const start = (this._page-1)*this._perPage+1, end = Math.min(this._page*this._perPage,total);
    document.getElementById('tonnage-count').textContent = total ? `${start}–${end} of ${total} vessels` : 'No results';

    const tbody = document.getElementById('tonnage-body');
    if (!records.length) {
      tbody.innerHTML = `<tr><td colspan="9"><div class="empty-state">
        <div class="empty-icon">🚢</div>
        <div class="empty-text">No tonnage records yet</div>
        <div class="empty-sub">Process a tonnage email to see vessel data here</div>
      </div></td></tr>`;
    } else {
      tbody.innerHTML = records.map(r => `
        <tr>
          <td>
            <span style="font-weight:600;color:var(--gold)">${htmlEsc(r.vessel_name||'—')}</span>
            ${r.class_society ? `<br><span class="td-muted" style="font-size:11px">${htmlEsc(r.class_society)}</span>` : ''}
          </td>
          <td class="td-mono">${htmlEsc(r.vessel_size||'—')}</td>
          <td>
            <span style="color:var(--blue)">${htmlEsc(r.open_port||'—')}</span>
          </td>
          <td class="td-muted">${htmlEsc(r.open_date||'—')}</td>
          <td class="td-muted">${htmlEsc(r.flag||'—')}</td>
          <td class="td-mono">${htmlEsc(r.built_year||'—')}</td>
          <td><span style="font-size:12px;color:var(--text-secondary)">${htmlEsc(r.vessel_type||'—')}</span></td>
          <td class="td-muted" style="font-size:12px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="${htmlEsc(r.account_name||'')}">${htmlEsc(r.account_name||'—')}</td>
          <td>
            <div class="action-cell">
              <button class="btn btn-ghost btn-sm btn-icon-only" title="View Source Email" onclick="viewEmailSource(${r.email_id}, '${htmlEsc(r.vessel_name || 'Vessel')}')">✉</button>
              <button class="btn btn-ghost btn-sm btn-icon-only" title="Edit" onclick="TonnageView.edit(${r.id})">✎</button>
              <button class="btn btn-danger btn-sm btn-icon-only" title="Delete" onclick="TonnageView.delete(${r.id})">🗑</button>
            </div>
          </td>
        </tr>`).join('');
    }

    const pages = Math.ceil(total/this._perPage);
    const pg = document.getElementById('tonnage-pagination');
    if (pages <= 1) { pg.innerHTML=''; return; }
    pg.innerHTML = `
      <span>${total} total</span>
      <div class="pagination-controls">
        <button class="page-btn" ${this._page<=1?'disabled':''} onclick="TonnageView.goPage(${this._page-1})">‹</button>
        ${Array.from({length:Math.min(pages,7)},(_,i)=>`
          <button class="page-btn ${i+1===this._page?'active':''}" onclick="TonnageView.goPage(${i+1})">${i+1}</button>`).join('')}
        <button class="page-btn" ${this._page>=pages?'disabled':''} onclick="TonnageView.goPage(${this._page+1})">›</button>
      </div>`;
  },

  onSearch: debounce(function(v){ TonnageView._search=v; TonnageView._page=1; TonnageView.load(); }, 350),
  goPage(p) { this._page=p; this.load(); },

  edit(id) {
    // Find record in DOM — re-fetch via API is cleaner
    API.get(`/tonnage/${id}`).then(r => {
      const fields = [
        ['vessel_name','Vessel Name',r.vessel_name],
        ['open_port','Open Port',r.open_port],
        ['open_date','Open Date',r.open_date],
        ['vessel_size','Vessel Size (DWT)',r.vessel_size],
        ['vessel_type','Vessel Type',r.vessel_type],
        ['flag','Flag',r.flag],
        ['built_year','Built Year',r.built_year],
        ['account_name','Account',r.account_name],
      ];
      showEditModal('Edit Tonnage Record', fields, async (form) => {
        await API.updateTonnage(id, form);
        Toast.show('Record updated', 'success');
        TonnageView.load();
      });
    }).catch(e => Toast.show('Error: '+e.message,'error'));
  },

  async delete(id) {
    if (!confirm('Delete this tonnage record?')) return;
    try { await API.deleteTonnage(id); Toast.show('Deleted','success'); this.load(); }
    catch(e) { Toast.show('Error: '+e.message,'error'); }
  },
};
