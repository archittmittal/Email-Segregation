/* cargo_tc.js — Time Charter cargo records view */
const CargoTCView = {
  _page: 1, _total: 0, _perPage: 20, _search: '',

  render() {
    return `
      <div class="fade-in">
        <div class="table-card">
          <div class="table-toolbar">
            <div class="search-box">
              <span class="search-icon">⌕</span>
              <input type="text" class="search-input" id="tc-search"
                placeholder="Search cargo or port…" oninput="CargoTCView.onSearch(this.value)" />
            </div>
            <div style="display:flex;gap:8px;align-items:center">
              <span class="td-muted" id="tc-count" style="font-size:13px"></span>
              <button class="btn btn-ghost btn-sm" onclick="API.exportCargoTC()" title="Export to CSV">⬇ Export CSV</button>
            </div>
          </div>
          <div class="table-wrapper">
            <table>
              <thead><tr>
                <th>Cargo</th>
                <th>Delivery Port</th>
                <th>Redelivery Port</th>
                <th>Duration</th>
                <th>Laycan</th>
                <th>Type</th>
                <th>Account</th>
                <th>Actions</th>
              </tr></thead>
              <tbody id="tc-body">
                <tr><td colspan="8"><div class="loading-spinner"><div class="spinner"></div></div></td></tr>
              </tbody>
            </table>
          </div>
          <div class="pagination" id="tc-pagination"></div>
        </div>
      </div>`;
  },

  async init() { this._page=1; this._search=''; await this.load(); },

  async load() {
    try {
      const data = await API.cargoTC({ page:this._page, per_page:this._perPage, search:this._search });
      this._total = data.total;
      this._render(data.records, data.total);
    } catch(e) { Toast.show('Failed to load Cargo TC: '+e.message,'error'); }
  },

  _render(records, total) {
    const start=(this._page-1)*this._perPage+1, end=Math.min(this._page*this._perPage,total);
    document.getElementById('tc-count').textContent = total ? `${start}–${end} of ${total} cargos` : 'No results';

    const tbody=document.getElementById('tc-body');
    if (!records.length) {
      tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state">
        <div class="empty-icon">⏱</div>
        <div class="empty-text">No Cargo TC records yet</div>
        <div class="empty-sub">Process a time charter email to populate this table</div>
      </div></td></tr>`;
    } else {
      tbody.innerHTML = records.map(r => `
        <tr>
          <td><span style="font-weight:600;color:var(--purple)">${htmlEsc(r.cargo_name||'—')}</span></td>
          <td><span style="color:var(--green)">${htmlEsc(r.delivery_port||'—')}</span></td>
          <td><span style="color:var(--gold)">${htmlEsc(r.redelivery_port||'—')}</span></td>
          <td class="td-mono" style="font-size:12px">${htmlEsc(r.duration||'—')}</td>
          <td class="td-muted">${htmlEsc(r.laycan||'—')}</td>
          <td style="font-size:12px;color:var(--text-secondary)">${htmlEsc(r.cargo_type||'—')}</td>
          <td class="td-muted" style="font-size:12px;max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="${htmlEsc(r.account_name||'')}">${htmlEsc(r.account_name||'—')}</td>
          <td>
            <div class="action-cell">
              <button class="btn btn-ghost btn-sm btn-icon-only" title="View Source Email" onclick="viewEmailSource(${r.email_id}, '${htmlEsc(r.cargo_name || 'Cargo TC')}')">✉</button>
              <button class="btn btn-ghost btn-sm btn-icon-only" title="Edit" onclick="CargoTCView.edit(${r.id})">✎</button>
              <button class="btn btn-danger btn-sm btn-icon-only" title="Delete" onclick="CargoTCView.delete(${r.id})">🗑</button>
            </div>
          </td>
        </tr>`).join('');
    }

    const pages=Math.ceil(total/this._perPage);
    const pg=document.getElementById('tc-pagination');
    if(pages<=1){pg.innerHTML='';return;}
    pg.innerHTML=`
      <span>${total} total</span>
      <div class="pagination-controls">
        <button class="page-btn" ${this._page<=1?'disabled':''} onclick="CargoTCView.goPage(${this._page-1})">‹</button>
        ${Array.from({length:Math.min(pages,7)},(_,i)=>`
          <button class="page-btn ${i+1===this._page?'active':''}" onclick="CargoTCView.goPage(${i+1})">${i+1}</button>`).join('')}
        <button class="page-btn" ${this._page>=pages?'disabled':''} onclick="CargoTCView.goPage(${this._page+1})">›</button>
      </div>`;
  },

  onSearch: debounce(function(v){ CargoTCView._search=v; CargoTCView._page=1; CargoTCView.load(); }, 350),
  goPage(p) { this._page=p; this.load(); },

  edit(id) {
    API.get(`/cargo_tc/${id}`).then(r => {
      const fields = [
        ['cargo_name','Cargo Name',r.cargo_name],
        ['delivery_port','Delivery Port',r.delivery_port],
        ['redelivery_port','Redelivery Port',r.redelivery_port],
        ['duration','Duration',r.duration],
        ['laycan','Laycan',r.laycan],
        ['cargo_type','Cargo Type',r.cargo_type],
        ['account_name','Account',r.account_name],
      ];
      showEditModal('Edit Cargo TC Record', fields, async (form) => {
        await API.updateCargoTC(id, form);
        Toast.show('Record updated','success');
        CargoTCView.load();
      });
    }).catch(e => Toast.show('Error: '+e.message,'error'));
  },

  async delete(id) {
    if (!confirm('Delete this cargo TC record?')) return;
    try { await API.deleteCargoTC(id); Toast.show('Deleted','success'); this.load(); }
    catch(e) { Toast.show('Error: '+e.message,'error'); }
  },
};
