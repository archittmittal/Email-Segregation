/* dashboard.js — Overview dashboard view */
const DashboardView = {
  _stats: null,

  render() {
    return `
      <div class="fade-in">
        <div class="stats-grid" id="stats-grid">
          ${[0,1,2,3].map(() => `
            <div class="stat-card">
              <div class="stat-header"><span class="stat-label">Loading…</span></div>
              <div class="stat-number" style="color:var(--text-muted)">—</div>
            </div>`).join('')}
        </div>

        <div class="card" style="margin-bottom: 24px; padding: 0; overflow: hidden;">
          <div id="market-map"></div>
        </div>

        <div class="two-col">
          <div>
            <div class="section-header">
              <h2 class="section-title">Recent Emails</h2>
              <a href="#inbox" class="btn btn-ghost btn-sm" onclick="App.navigate('inbox')">View all →</a>
            </div>
            <div class="table-card">
              <div class="table-wrapper">
                <table id="recent-table">
                  <thead><tr>
                    <th>Subject</th><th>Category</th><th>Confidence</th><th>Date</th>
                  </tr></thead>
                  <tbody id="recent-body">
                    <tr><td colspan="4" class="empty-state">
                      <div class="empty-icon">✉</div>
                      <div class="empty-text">Loading recent emails…</div>
                    </td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div>
            <div class="section-header">
              <h2 class="section-title">Category Breakdown</h2>
            </div>
            <div class="card">
              <div id="chart-area">
                <div class="loading-spinner" style="height:120px">
                  <div class="spinner"></div>
                </div>
              </div>
            </div>

            <div class="section-header" style="margin-top:20px">
              <h2 class="section-title">Quick Actions</h2>
            </div>
            <div class="card" style="display:flex;flex-direction:column;gap:10px">
              <button class="btn btn-primary" onclick="App.openUploadModal()" style="width:100%;justify-content:center">
                <span class="btn-icon">+</span> Process New Email
              </button>
              <button class="btn btn-ghost" onclick="App.navigate('tonnage')" style="width:100%;justify-content:center">
                🚢 View All Tonnage Records
              </button>
              <button class="btn btn-ghost" onclick="App.navigate('cargo-vc')" style="width:100%;justify-content:center">
                📦 View All Cargo VC Records
              </button>
              <button class="btn btn-ghost" onclick="App.navigate('cargo-tc')" style="width:100%;justify-content:center">
                ⏱ View All Cargo TC Records
              </button>
            </div>
          </div>
        </div>
      </div>`;
  },

  async init() {
    try {
      const stats = await API.stats();
      this._stats = stats;
      this._renderStats(stats);
      this._renderRecent(stats.recent || []);
      this._renderChart(stats);
      App.updateBadges(stats);
      
      const mapData = await API._req('GET', '/map');
      if (mapData && mapData.markers) {
        this._renderMap(mapData.markers);
      }
    } catch (e) {
      Toast.show('Failed to load dashboard data: ' + e.message, 'error');
    }
  },

  _renderStats(s) {
    document.getElementById('stats-grid').innerHTML = `
      <div class="stat-card green">
        <div class="stat-header">
          <span class="stat-label">Total Emails</span>
          <span class="stat-icon">✉</span>
        </div>
        <div class="stat-number">${s.total_emails}</div>
        <div class="stat-sub">All ingested emails</div>
      </div>
      <div class="stat-card gold">
        <div class="stat-header">
          <span class="stat-label">Tonnage</span>
          <span class="stat-icon">🚢</span>
        </div>
        <div class="stat-number">${s.tonnage_records}</div>
        <div class="stat-sub">Vessel records</div>
      </div>
      <div class="stat-card blue">
        <div class="stat-header">
          <span class="stat-label">Cargo VC</span>
          <span class="stat-icon">📦</span>
        </div>
        <div class="stat-number">${s.cargo_vc_records}</div>
        <div class="stat-sub">Voyage charter cargos</div>
      </div>
      <div class="stat-card purple">
        <div class="stat-header">
          <span class="stat-label">Cargo TC</span>
          <span class="stat-icon">⏱</span>
        </div>
        <div class="stat-number">${s.cargo_tc_records}</div>
        <div class="stat-sub">Time charter cargos</div>
      </div>`;
  },

  _renderRecent(emails) {
    const tbody = document.getElementById('recent-body');
    if (!emails.length) {
      tbody.innerHTML = `<tr><td colspan="4">
        <div class="empty-state">
          <div class="empty-icon">✉</div>
          <div class="empty-text">No emails yet</div>
          <div class="empty-sub">Click "Process Email" to get started</div>
        </div>
      </td></tr>`;
      return;
    }
    tbody.innerHTML = emails.map(e => `
      <tr>
        <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
            title="${htmlEsc(e.subject || '')}">${htmlEsc(e.subject || 'No Subject')}</td>
        <td><span class="badge badge-${e.category}">${catLabel(e.category)}</span></td>
        <td><span class="conf-pill">${(e.confidence*100).toFixed(0)}%</span></td>
        <td class="td-muted">${fmtDate(e.created_at)}</td>
      </tr>`).join('');
  },

  _renderChart(s) {
    const total = s.total_emails || 1;
    const cats = [
      { key: 'tonnage',  label: 'Tonnage',  color: 'gold',   val: (s.by_category.tonnage  || 0) },
      { key: 'cargo_vc', label: 'Cargo VC', color: 'blue',   val: (s.by_category.cargo_vc || 0) },
      { key: 'cargo_tc', label: 'Cargo TC', color: 'purple', val: (s.by_category.cargo_tc || 0) },
    ];
    document.getElementById('chart-area').innerHTML = cats.map(c => `
      <div class="chart-bar-row">
        <span class="chart-bar-label">${c.label}</span>
        <div class="chart-bar-track">
          <div class="chart-bar-fill ${c.color}" style="width:0%" data-pct="${Math.round(c.val/total*100)}"></div>
        </div>
        <span class="chart-bar-count">${c.val}</span>
      </div>`).join('');
    // Animate bars after render
    requestAnimationFrame(() => {
      document.querySelectorAll('.chart-bar-fill').forEach(el => {
        el.style.width = el.dataset.pct + '%';
      });
    });
  },

  _renderMap(markers) {
    if (this._map) {
      this._map.remove();
      this._map = null;
    }
    
    // Default center to a global view (Atlantic/Africa to see East & West)
    this._map = L.map('market-map').setView([20, 0], 2);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this._map);

    const colors = {
      tonnage: '#ffc107',  // Gold
      cargo_vc: '#0d6efd', // Blue
      cargo_tc: '#6f42c1'  // Purple
    };
    
    const emojis = {
      tonnage: '🚢',
      cargo_vc: '📦',
      cargo_tc: '⏱'
    };

    markers.forEach(m => {
      const color = colors[m.type] || '#ccc';
      const iconHtml = `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);"></div>`;
      
      const customIcon = L.divIcon({
        className: 'custom-map-marker',
        html: iconHtml,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      });

      L.marker([m.lat, m.lon], { icon: customIcon })
        .bindPopup(`
          <div style="font-size: 13px; margin: -5px;">
            <strong style="color:var(--text-primary); font-size: 14px;">${emojis[m.type]} ${m.title}</strong><br>
            <span style="color:var(--text-muted); font-size: 12px;">${m.subtitle}</span><br>
            <span style="color:var(--text-muted); font-size: 11px;">${m.date}</span>
          </div>
        `)
        .addTo(this._map);
    });
  }
};
