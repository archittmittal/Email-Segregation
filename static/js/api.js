/* api.js — Fetch wrappers for all backend endpoints */
const API = {
  BASE: '/api',

  async _req(method, path, body = null, params = {}) {
    const url = new URL(this.BASE + path, window.location.origin);
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== '') url.searchParams.set(k, v); });
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    
    let data = {};
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        data = await res.json();
      } catch (err) {}
    } else {
      try {
        const text = await res.text();
        data = { error: text };
      } catch (err) {}
    }

    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  },

  get:    (path, params) => API._req('GET',    path, null, params),
  post:   (path, body)   => API._req('POST',   path, body),
  patch:  (path, body)   => API._req('PATCH',  path, body),
  delete: (path)         => API._req('DELETE', path),

  // ── Domain helpers ─────────────────────────────────────────────
  stats:       ()       => API.get('/stats'),
  history:     ()       => API.get('/history'),
  emails:      (p)      => API.get('/emails',   p),
  emailById:   (id)     => API.get(`/emails/${id}`),
  processEmail:(body)   => API.post('/emails',  body),
  deleteEmail: (id)     => API.delete(`/emails/${id}`),

  // File upload (multipart)
  uploadEmail: (formData) => {
    return fetch('/api/emails/upload', { method: 'POST', body: formData })
      .then(res => res.json().then(data => {
        if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
        return data;
      }));
  },

  tonnage:         (p)      => API.get('/tonnage',       p),
  updateTonnage:   (id, b)  => API.patch(`/tonnage/${id}`, b),
  deleteTonnage:   (id)     => API.delete(`/tonnage/${id}`),

  cargoVC:         (p)      => API.get('/cargo_vc',      p),
  updateCargoVC:   (id, b)  => API.patch(`/cargo_vc/${id}`, b),
  deleteCargoVC:   (id)     => API.delete(`/cargo_vc/${id}`),

  cargoTC:         (p)      => API.get('/cargo_tc',      p),
  updateCargoTC:   (id, b)  => API.patch(`/cargo_tc/${id}`, b),
  deleteCargoTC:   (id)     => API.delete(`/cargo_tc/${id}`),

  // Matching engine
  matches: (p) => API.get('/matches', p),

  // CSV export — triggers browser download
  exportCSV(path, filename) {
    const url = `/api${path}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  },
  exportTonnage:  () => API.exportCSV('/tonnage/export',  'tonnage_export.csv'),
  exportCargoVC:  () => API.exportCSV('/cargo_vc/export', 'cargo_vc_export.csv'),
  exportCargoTC:  () => API.exportCSV('/cargo_tc/export', 'cargo_tc_export.csv'),
};
