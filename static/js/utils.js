/* utils.js — Global helper utilities for ShipSeg */

function htmlEsc(str) {
  return String(str ?? '')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;')
    .replace(/'/g,'&#39;');
}

function fmtDate(iso) {
  if (!iso) return '—';
  try {
    let dateStr = iso;
    if (typeof dateStr === 'string' && !dateStr.endsWith('Z') && !dateStr.includes('+') && !/[-+]\d{2}:?\d{2}$/.test(dateStr)) {
      dateStr = dateStr + 'Z';
    }
    return new Date(dateStr).toLocaleDateString('en-GB', { day:'numeric', month:'short', year:'2-digit', hour:'2-digit', minute:'2-digit' });
  } catch { return iso; }
}

function catLabel(cat) {
  return { tonnage:'Tonnage', cargo_vc:'Cargo VC', cargo_tc:'Cargo TC', unknown:'Unknown' }[cat] || cat;
}

function debounce(fn, ms) {
  let t;
  return function(...args) { clearTimeout(t); t = setTimeout(() => fn.apply(this, args), ms); };
}

// ── Toast ─────────────────────────────────────────────────────────
const Toast = {
  show(msg, type = 'info', duration = 3500) {
    const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `<span class="toast-icon">${icons[type]||'ℹ'}</span><span class="toast-msg">${htmlEsc(msg)}</span>`;
    const container = document.getElementById('toast-container');
    container.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.3s';
      setTimeout(() => el.remove(), 300);
    }, duration);
  },
};

// ── Shared edit modal ─────────────────────────────────────────────
function showEditModal(title, fields, onSave) {
  const existing = document.getElementById('edit-modal-overlay');
  if (existing) existing.remove();

  const overlay = document.createElement('div');
  overlay.id = 'edit-modal-overlay';
  overlay.className = 'modal-overlay open';
  overlay.innerHTML = `
    <div class="modal" style="max-width:560px">
      <div class="modal-header">
        <h2 class="modal-title">${htmlEsc(title)}</h2>
        <button class="modal-close" onclick="document.getElementById('edit-modal-overlay').remove()">✕</button>
      </div>
      <div class="modal-body">
        ${fields.map(([key, label, val]) => `
          <div class="form-group">
            <label class="form-label" for="edit-${key}">${htmlEsc(label)}</label>
            <input type="text" id="edit-${key}" class="form-input"
              value="${htmlEsc(val||'')}" data-key="${key}" />
          </div>`).join('')}
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="document.getElementById('edit-modal-overlay').remove()">Cancel</button>
        <button class="btn btn-primary" id="edit-save-btn">Save Changes</button>
      </div>
    </div>`;

  overlay.onclick = e => { if (e.target === overlay) overlay.remove(); };
  document.body.appendChild(overlay);

  document.getElementById('edit-save-btn').onclick = async () => {
    const form = {};
    overlay.querySelectorAll('[data-key]').forEach(el => {
      form[el.dataset.key] = el.value.trim() || null;
    });
    const btn = document.getElementById('edit-save-btn');
    btn.textContent = 'Saving…';
    btn.disabled = true;
    try {
      await onSave(form);
      overlay.remove();
    } catch(e) {
      Toast.show('Save failed: ' + e.message, 'error');
      btn.textContent = 'Save Changes';
      btn.disabled = false;
    }
  };
}
