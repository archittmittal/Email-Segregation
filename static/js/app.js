/* app.js — SPA router, upload modal logic */


// ── SPA Router ────────────────────────────────────────────────────
const VIEWS = {
  'dashboard': { view: DashboardView, title: 'Dashboard',        breadcrumb: 'Overview' },
  'inbox':     { view: InboxView,     title: 'Email Inbox',      breadcrumb: 'All Emails' },
  'tonnage':   { view: TonnageView,   title: 'Tonnage',          breadcrumb: 'Open Vessels' },
  'cargo-vc':  { view: CargoVCView,   title: 'Cargo VC',         breadcrumb: 'Voyage Charter Cargos' },
  'cargo-tc':  { view: CargoTCView,   title: 'Cargo TC',         breadcrumb: 'Time Charter Cargos' },
  'matching':  { view: MatchingView,  title: 'Matching Engine',  breadcrumb: 'Vessel ↔ Cargo Matches' },
  'history':   { view: HistoryView,   title: 'Broker History',   breadcrumb: 'Activity Timeline' },
};

const App = {
  _current: 'dashboard',
  _activeTab: 'paste',     // 'paste' | 'file'
  _selectedFile: null,

  init() {
    window.addEventListener('hashchange', () => this._handleRoute());
    document.querySelectorAll('.nav-item').forEach(el => {
      el.addEventListener('click', e => {
        e.preventDefault();
        this.navigate(el.dataset.view);
      });
    });

    // Drag-and-drop on file zone
    const zone = document.getElementById('file-drop-zone');
    if (zone) {
      zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
      zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
      zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file) this._setFile(file);
      });
    }

    this._handleRoute();
  },

  _handleRoute() {
    const hash = window.location.hash.replace('#', '') || 'dashboard';
    const key = VIEWS[hash] ? hash : 'dashboard';
    this._render(key);
  },

  navigate(viewKey) {
    if (window.location.hash === '#' + viewKey) {
      this._render(viewKey);
    } else {
      window.location.hash = viewKey;
    }
  },

  _render(key) {
    this._current = key;
    const def = VIEWS[key];
    if (!def) return;

    document.querySelectorAll('.nav-item').forEach(el => {
      el.classList.toggle('active', el.dataset.view === key);
    });

    document.getElementById('page-title').textContent = def.title;
    document.getElementById('breadcrumb').textContent = def.breadcrumb;

    const content = document.getElementById('app-content');
    content.innerHTML = def.view.render();
    def.view.init();
  },

  updateBadges(stats) {
    const t  = stats.total_emails    || 0;
    const tv = stats.tonnage_records  || 0;
    const vc = stats.cargo_vc_records || 0;
    const tc = stats.cargo_tc_records || 0;
    document.getElementById('badge-inbox').textContent   = t;
    document.getElementById('badge-tonnage').textContent = tv;
    document.getElementById('badge-vc').textContent      = vc;
    document.getElementById('badge-tc').textContent      = tc;
  },

  // ── Upload modal ─────────────────────────────────────────────────
  openUploadModal(tab = 'paste') {
    document.getElementById('modal-overlay').classList.add('open');
    document.getElementById('classifier-preview').style.display = 'none';
    document.getElementById('duplicate-warning').style.display  = 'none';
    document.getElementById('email-subject').value = '';
    document.getElementById('email-sender').value  = '';
    document.getElementById('email-text').value    = '';
    document.getElementById('upload-subject').value = '';
    document.getElementById('upload-sender').value  = '';
    this._selectedFile = null;
    document.getElementById('file-drop-name').style.display = 'none';
    document.getElementById('file-drop-name').textContent = '';
    this.switchTab(tab);
    if (tab === 'paste') document.getElementById('email-text').focus();
  },

  closeUploadModal(event, force = false) {
    if (force || !event || event.target === document.getElementById('modal-overlay')) {
      document.getElementById('modal-overlay').classList.remove('open');
    }
  },

  switchTab(tab) {
    this._activeTab = tab;
    document.getElementById('tab-content-paste').style.display = tab === 'paste' ? '' : 'none';
    document.getElementById('tab-content-file').style.display  = tab === 'file'  ? '' : 'none';
    document.getElementById('tab-paste').classList.toggle('active', tab === 'paste');
    document.getElementById('tab-file').classList.toggle('active',  tab === 'file');
    document.getElementById('classifier-preview').style.display = 'none';
    document.getElementById('duplicate-warning').style.display  = 'none';
  },

  onFileSelected(input) {
    const file = input.files[0];
    if (file) this._setFile(file);
  },

  _setFile(file) {
    this._selectedFile = file;
    const nameEl = document.getElementById('file-drop-name');
    nameEl.textContent = `📄 ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    nameEl.style.display = 'block';
  },

  // ── Submit (paste tab) ───────────────────────────────────────────
  async submitEmail() {
    if (this._activeTab === 'file') {
      return this._submitFile();
    }

    const text    = document.getElementById('email-text').value.trim();
    const subject = document.getElementById('email-subject').value.trim();
    const sender  = document.getElementById('email-sender').value.trim();

    if (!text) { Toast.show('Please paste email text', 'error'); return; }

    const btn = document.getElementById('btn-submit-email');
    const btnText = document.getElementById('btn-submit-text');
    btn.disabled = true;
    btnText.textContent = 'Processing…';

    try {
      const result = await API.processEmail({ text, subject, sender });
      this._showResult(result);
    } catch(e) {
      Toast.show('Error: ' + e.message, 'error');
    } finally {
      btn.disabled = false;
      btnText.textContent = 'Classify & Extract';
    }
  },

  // ── Submit (file tab) ────────────────────────────────────────────
  async _submitFile() {
    if (!this._selectedFile) { Toast.show('Please choose a file', 'error'); return; }

    const btn = document.getElementById('btn-submit-email');
    const btnText = document.getElementById('btn-submit-text');
    btn.disabled = true;
    btnText.textContent = 'Uploading…';

    try {
      const fd = new FormData();
      fd.append('file', this._selectedFile);
      const subject = document.getElementById('upload-subject').value.trim();
      const sender  = document.getElementById('upload-sender').value.trim();
      if (subject) fd.append('subject', subject);
      if (sender)  fd.append('sender',  sender);

      const result = await API.uploadEmail(fd);
      this._showResult(result);
    } catch(e) {
      Toast.show('Upload error: ' + e.message, 'error');
    } finally {
      btn.disabled = false;
      btnText.textContent = 'Classify & Extract';
    }
  },

  // ── Shared result handler ────────────────────────────────────────
  _showResult(result) {
    const preview = document.getElementById('classifier-preview');
    const badge   = document.getElementById('preview-badge');
    const conf    = document.getElementById('preview-confidence');
    const dupWarn = document.getElementById('duplicate-warning');

    preview.style.display = 'flex';
    badge.textContent = catLabel(result.category).toUpperCase();
    badge.style.color = {
      tonnage: 'var(--gold)', cargo_vc: 'var(--blue)', cargo_tc: 'var(--purple)',
    }[result.category] || 'var(--text-muted)';
    conf.textContent = `${(result.confidence * 100).toFixed(0)}% confidence`;

    if (result.is_duplicate) {
      dupWarn.style.display = 'block';
      Toast.show('⚠ Duplicate email detected and flagged', 'warning', 4500);
    } else {
      const count = result.extracted?.length || 0;
      Toast.show(`✓ Classified as ${catLabel(result.category)} · ${count} record${count!==1?'s':''} extracted`, 'success');
    }

    setTimeout(() => {
      this.closeUploadModal(null, true);
      this.navigate(this._current === 'dashboard' ? 'dashboard' : this._current);
      API.stats().then(s => this.updateBadges(s)).catch(() => {});
    }, 1400);
  },
};

// Boot
document.addEventListener('DOMContentLoaded', () => App.init());
