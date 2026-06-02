/* history.js — Per-broker / per-sender activity tracking */
const HistoryView = {
  _data: [],

  render() {
    return `
      <div class="fade-in">
        <div class="section-header" style="margin-bottom:16px">
          <h2 class="section-title">Broker Activity Timeline</h2>
          <span class="td-muted" id="history-count" style="font-size:13px"></span>
        </div>
        <div class="table-card">
          <div class="table-wrapper">
            <table>
              <thead><tr>
                <th>#</th>
                <th>Broker / Sender</th>
                <th>Emails</th>
                <th>Tonnage</th>
                <th>Cargo VC</th>
                <th>Cargo TC</th>
                <th>Unknown</th>
                <th>Last Seen</th>
              </tr></thead>
              <tbody id="history-body">
                <tr><td colspan="8"><div class="loading-spinner"><div class="spinner"></div></div></td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>`;
  },

  async init() {
    await this.load();
  },

  async load() {
    try {
      const data = await API.history();
      this._data = data.history || [];
      this._render();
    } catch(e) {
      Toast.show('Failed to load history: ' + e.message, 'error');
    }
  },

  _render() {
    const tbody = document.getElementById('history-body');
    const countEl = document.getElementById('history-count');
    countEl.textContent = `${this._data.length} broker${this._data.length !== 1 ? 's' : ''}`;

    if (!this._data.length) {
      tbody.innerHTML = `<tr><td colspan="8">
        <div class="empty-state">
          <div class="empty-icon">📅</div>
          <div class="empty-text">No broker history yet</div>
          <div class="empty-sub">Process some emails to see activity here</div>
        </div></td></tr>`;
      return;
    }

    tbody.innerHTML = this._data.map((row, i) => {
      const cats = row.categories || {};
      const tonnage  = cats.tonnage   || 0;
      const cargoVc  = cats.cargo_vc  || 0;
      const cargoTc  = cats.cargo_tc  || 0;
      const unknown  = cats.unknown   || 0;
      return `
        <tr>
          <td class="td-muted td-mono">${i + 1}</td>
          <td>
            <div style="font-weight:500">${htmlEsc(row.sender || '—')}</div>
          </td>
          <td><span class="conf-pill">${row.total}</span></td>
          <td>${tonnage  ? `<span class="badge badge-tonnage">${tonnage}</span>`   : '<span class="td-muted">—</span>'}</td>
          <td>${cargoVc  ? `<span class="badge badge-cargo_vc">${cargoVc}</span>`  : '<span class="td-muted">—</span>'}</td>
          <td>${cargoTc  ? `<span class="badge badge-cargo_tc">${cargoTc}</span>`  : '<span class="td-muted">—</span>'}</td>
          <td>${unknown  ? `<span class="td-muted">${unknown}</span>`               : '<span class="td-muted">—</span>'}</td>
          <td class="td-muted">${fmtDate(row.last_seen)}</td>
        </tr>`;
    }).join('');
  },
};
