/* cargo_vc.js — Voyage Charter cargo records view */
const CargoVCView = {
  _page: 1, _total: 0, _perPage: 20, _search: '',

  render() {
    return `
      <div class="fade-in">
        <div class="table-card">
          <div class="table-toolbar">
            <div class="search-box">
              <span class="search-icon">⌕</span>
              <input type="text" class="search-input" id="vc-search"
                placeholder="Search cargo or port…" oninput="CargoVCView.onSearch(this.value)" />
            </div>
            <div style="display:flex;gap:8px;align-items:center">
              <span class="td-muted" id="vc-count" style="font-size:13px"></span>
              <button class="btn btn-ghost btn-sm" onclick="API.exportCargoVC()" title="Export to CSV">⬇ Export CSV</button>
            </div>
          </div>
          <div class="table-wrapper">
            <table>
              <thead><tr>
                <th>Cargo</th>
                <th>Quantity</th>
                <th>Loading Port</th>
                <th>Discharge Port</th>
                <th>Laycan</th>
                <th>Type</th>
                <th>Account</th>
                <th>Actions</th>
              </tr></thead>
              <tbody id="vc-body">
                <tr><td colspan="8"><div class="loading-spinner"><div class="spinner"></div></div></td></tr>
              </tbody>
            </table>
          </div>
          <div class="pagination" id="vc-pagination"></div>
        </div>
      </div>`;
  },

  async init() { this._page=1; this._search=''; await this.load(); },

  async load() {
    try {
      const data = await API.cargoVC({ page:this._page, per_page:this._perPage, search:this._search });
      this._total = data.total;
      this._render(data.records, data.total);
    } catch(e) { Toast.show('Failed to load Cargo VC: '+e.message,'error'); }
  },

  _render(records, total) {
    const start=(this._page-1)*this._perPage+1, end=Math.min(this._page*this._perPage,total);
    document.getElementById('vc-count').textContent = total ? `${start}–${end} of ${total} cargos` : 'No results';

    const tbody = document.getElementById('vc-body');
    if (!records.length) {
      tbody.innerHTML = `<tr><td colspan="8"><div class="empty-state">
        <div class="empty-icon">📦</div>
        <div class="empty-text">No Cargo VC records yet</div>
        <div class="empty-sub">Process a voyage charter cargo email to populate this table</div>
      </div></td></tr>`;
    } else {
      tbody.innerHTML = records.map(r => `
        <tr>
          <td><span style="font-weight:600;color:var(--blue)">${htmlEsc(r.cargo_name||'—')}</span></td>
          <td class="td-mono" style="font-size:12px">${htmlEsc(r.quantity||'—')}</td>
          <td><span style="color:var(--green)">${htmlEsc(r.loading_port||'—')}</span></td>
          <td><span style="color:var(--gold)">${htmlEsc(r.discharge_port||'—')}</span></td>
          <td class="td-muted">${htmlEsc(r.laycan||'—')}</td>
          <td><span style="font-size:12px;color:var(--text-secondary)">${htmlEsc(r.cargo_type||'—')}</span></td>
          <td class="td-muted" style="font-size:12px;max-width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
              title="${htmlEsc(r.account_name||'')}">${htmlEsc(r.account_name||'—')}</td>
          <td>
            <div class="action-cell">
              <button class="btn btn-ghost btn-sm btn-icon-only" title="View Source Email" onclick="viewEmailSource(${r.email_id})">✉</button>
              <button class="btn btn-ghost btn-sm btn-icon-only" title="Edit" onclick="CargoVCView.edit(${r.id})">✎</button>
              <button class="btn btn-danger btn-sm btn-icon-only" title="Delete" onclick="CargoVCView.delete(${r.id})">🗑</button>
            </div>
          </td>
        </tr>`).join('');
    }

    const pages=Math.ceil(total/this._perPage);
    const pg=document.getElementById('vc-pagination');
    if(pages<=1){pg.innerHTML='';return;}
    pg.innerHTML=`
      <span>${total} total</span>
      <div class="pagination-controls">
        <button class="page-btn" ${this._page<=1?'disabled':''} onclick="CargoVCView.goPage(${this._page-1})">‹</button>
        ${Array.from({length:Math.min(pages,7)},(_,i)=>`
          <button class="page-btn ${i+1===this._page?'active':''}" onclick="CargoVCView.goPage(${i+1})">${i+1}</button>`).join('')}
        <button class="page-btn" ${this._page>=pages?'disabled':''} onclick="CargoVCView.goPage(${this._page+1})">›</button>
      </div>`;
  },

  onSearch: debounce(function(v){ CargoVCView._search=v; CargoVCView._page=1; CargoVCView.load(); }, 350),
  goPage(p) { this._page=p; this.load(); },

  edit(id) {
    API.get(`/cargo_vc/${id}`).then(r => {
      const fields = [
        ['cargo_name','Cargo Name',r.cargo_name],
        ['quantity','Quantity',r.quantity],
        ['loading_port','Loading Port',r.loading_port],
        ['discharge_port','Discharge Port',r.discharge_port],
        ['laycan','Laycan',r.laycan],
        ['cargo_type','Cargo Type',r.cargo_type],
        ['account_name','Account',r.account_name],
      ];
      showEditModal('Edit Cargo VC Record', fields, async (form) => {
        await API.updateCargoVC(id, form);
        Toast.show('Record updated','success');
        CargoVCView.load();
      });
    }).catch(e => Toast.show('Error: '+e.message,'error'));
  },

  async delete(id) {
    if (!confirm('Delete this cargo VC record?')) return;
    try { await API.deleteCargoVC(id); Toast.show('Deleted','success'); this.load(); }
    catch(e) { Toast.show('Error: '+e.message,'error'); }
  },
};
