/* matching.js — Vessel ↔ Cargo matching engine view */
const MatchingView = {
  _vessels: [],
  _selectedVessel: null,
  _mode: 'vc',   // 'vc' | 'tc'

  render() {
    return `
      <div class="fade-in">
        <div class="two-col matching-layout">

          <!-- LEFT: Vessel selector -->
          <div>
            <div class="section-header">
              <h2 class="section-title">Open Vessels</h2>
              <div class="mode-toggle" id="match-mode-toggle">
                <button class="mode-btn active" id="mode-vc" onclick="MatchingView.setMode('vc')">vs Cargo VC</button>
                <button class="mode-btn" id="mode-tc" onclick="MatchingView.setMode('tc')">vs Cargo TC</button>
              </div>
            </div>
            <div class="table-card vessel-list" id="vessel-list">
              <div class="loading-spinner"><div class="spinner"></div></div>
            </div>
          </div>

          <!-- RIGHT: Match results -->
          <div>
            <div class="section-header">
              <h2 class="section-title" id="match-title">Select a vessel to see matches</h2>
            </div>
            <div id="match-results">
              <div class="empty-state" style="padding:48px 24px">
                <div class="empty-icon">🔗</div>
                <div class="empty-text">No vessel selected</div>
                <div class="empty-sub">Click any vessel on the left to see ranked cargo matches</div>
              </div>
            </div>
          </div>

        </div>
      </div>`;
  },

  async init() {
    this._selectedVessel = null;
    await this._loadVessels();
  },

  async _loadVessels() {
    try {
      const data = await API.tonnage({ per_page: 100 });
      this._vessels = data.records || [];
      this._renderVesselList();
    } catch(e) {
      Toast.show('Failed to load vessels: ' + e.message, 'error');
    }
  },

  _renderVesselList() {
    const el = document.getElementById('vessel-list');
    if (!this._vessels.length) {
      el.innerHTML = `<div class="empty-state"><div class="empty-icon">🚢</div><div class="empty-text">No vessel records yet</div></div>`;
      return;
    }
    el.innerHTML = this._vessels.map(v => `
      <div class="vessel-card ${this._selectedVessel === v.id ? 'selected' : ''}"
           id="vessel-card-${v.id}"
           onclick="MatchingView.selectVessel(${v.id})">
        <div class="vessel-card-name">${htmlEsc(v.vessel_name || '—')}</div>
        <div class="vessel-card-meta">
          <span style="color:var(--blue)">${htmlEsc(v.open_port || '—')}</span>
          <span class="td-muted">·</span>
          <span class="td-muted">${htmlEsc(v.open_date || '—')}</span>
          <span class="td-muted">·</span>
          <span class="td-mono" style="font-size:11px">${htmlEsc(v.vessel_size || '—')}</span>
        </div>
      </div>`).join('');
  },

  setMode(mode) {
    this._mode = mode;
    document.getElementById('mode-vc').classList.toggle('active', mode === 'vc');
    document.getElementById('mode-tc').classList.toggle('active', mode === 'tc');
    if (this._selectedVessel) this.selectVessel(this._selectedVessel);
  },

  async selectVessel(id) {
    this._selectedVessel = id;
    // Highlight selection
    document.querySelectorAll('.vessel-card').forEach(el => el.classList.remove('selected'));
    const card = document.getElementById(`vessel-card-${id}`);
    if (card) card.classList.add('selected');

    const vessel = this._vessels.find(v => v.id === id);
    const title  = document.getElementById('match-title');
    if (vessel) title.textContent = `Matches for ${vessel.vessel_name}`;

    const resultsEl = document.getElementById('match-results');
    resultsEl.innerHTML = `<div class="loading-spinner" style="height:120px"><div class="spinner"></div></div>`;

    try {
      const mode = this._mode === 'vc' ? 'tonnage_to_vc' : 'tonnage_to_tc';
      const data = await API.matches({ mode, id });
      const matches = data.matches || [];
      this._renderMatches(matches, this._mode);
    } catch(e) {
      Toast.show('Match error: ' + e.message, 'error');
      resultsEl.innerHTML = `<div class="empty-state"><div class="empty-text">Error loading matches</div></div>`;
    }
  },

  _renderMatches(matches, mode) {
    const el = document.getElementById('match-results');
    if (!matches.length) {
      el.innerHTML = `<div class="empty-state" style="padding:48px 24px">
        <div class="empty-icon">📭</div>
        <div class="empty-text">No cargo records to match against</div>
        <div class="empty-sub">Process some cargo emails first</div>
      </div>`;
      return;
    }

    el.innerHTML = `<div class="match-list">` + matches.map(m => {
      const cargo = m.cargo_vc || m.cargo_tc;
      const score = m.score;
      const scoreClass = score >= 70 ? 'score-high' : score >= 40 ? 'score-mid' : 'score-low';
      const scoreLabel = score >= 70 ? 'Strong' : score >= 40 ? 'Possible' : 'Weak';

      const port = mode === 'vc'
        ? `<span style="color:var(--green)">${htmlEsc(cargo.loading_port || '—')}</span> → <span style="color:var(--gold)">${htmlEsc(cargo.discharge_port || '—')}</span>`
        : `<span style="color:var(--green)">${htmlEsc(cargo.delivery_port || '—')}</span> → <span style="color:var(--gold)">${htmlEsc(cargo.redelivery_port || '—')}</span>`;

      return `
        <div class="match-card">
          <div class="match-card-top">
            <div>
              <div class="match-cargo-name">${htmlEsc(cargo.cargo_name || 'Unknown Cargo')}</div>
              <div class="match-ports">${port}</div>
              <div class="match-meta td-muted">
                Laycan: ${htmlEsc(cargo.laycan || '—')}
                ${mode === 'vc' && cargo.quantity ? ` · ${htmlEsc(cargo.quantity)}` : ''}
                ${mode === 'tc' && cargo.duration ? ` · ${htmlEsc(cargo.duration)}` : ''}
                ${cargo.account_name ? ` · ${htmlEsc(cargo.account_name)}` : ''}
              </div>
            </div>
            <div class="match-score-block">
              <div class="match-score ${scoreClass}">${score}</div>
              <div class="match-score-label ${scoreClass}">${scoreLabel}</div>
            </div>
          </div>
          <div class="match-score-bar-track">
            <div class="match-score-bar ${scoreClass}" style="width:${score}%"></div>
          </div>
        </div>`;
    }).join('') + '</div>';
  },
};
