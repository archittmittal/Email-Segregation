/* analytics.js — Market trend & fleet breakdown analytics view */
const AnalyticsView = {
  _charts: [],

  render() {
    return `
      <div class="fade-in">
        <!-- KPI Row -->
        <div class="stats-grid" id="analytics-kpi-grid" style="margin-bottom: 24px;">
          <div class="stat-card green">
            <div class="stat-header">
              <span class="stat-label">Total Emails</span>
              <span class="stat-icon">✉</span>
            </div>
            <div class="stat-number" id="kpi-total-emails">—</div>
            <div class="stat-sub">Ingested dataset</div>
          </div>
          <div class="stat-card gold">
            <div class="stat-header">
              <span class="stat-label">Tonnage</span>
              <span class="stat-icon">🚢</span>
            </div>
            <div class="stat-number" id="kpi-tonnage">—</div>
            <div class="stat-sub">Open vessels</div>
          </div>
          <div class="stat-card blue">
            <div class="stat-header">
              <span class="stat-label">Cargo VC</span>
              <span class="stat-icon">📦</span>
            </div>
            <div class="stat-number" id="kpi-cargo-vc">—</div>
            <div class="stat-sub">Voyage charter cargos</div>
          </div>
          <div class="stat-card purple">
            <div class="stat-header">
              <span class="stat-label">Cargo TC</span>
              <span class="stat-icon">⏱</span>
            </div>
            <div class="stat-number" id="kpi-cargo-tc">—</div>
            <div class="stat-sub">Time charter cargos</div>
          </div>
        </div>

        <!-- 2x2 Chart Grid -->
        <div class="analytics-grid">
          <div class="card chart-card">
            <div class="card-header" style="border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 16px; font-weight:600; font-size:14px; color:var(--text-primary)">
              📈 Email Volume Trend (30 Days)
            </div>
            <div class="chart-container">
              <canvas id="chart-volume-trend"></canvas>
            </div>
          </div>

          <div class="card chart-card">
            <div class="card-header" style="border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 16px; font-weight:600; font-size:14px; color:var(--text-primary)">
              🍩 Category Distribution
            </div>
            <div class="chart-container" style="max-height: 280px; display: flex; justify-content: center;">
              <canvas id="chart-category-dist"></canvas>
            </div>
          </div>

          <div class="card chart-card">
            <div class="card-header" style="border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 16px; font-weight:600; font-size:14px; color:var(--text-primary)">
              🔥 Top Cargo Ports Activity
            </div>
            <div class="chart-container">
              <canvas id="chart-top-ports"></canvas>
            </div>
          </div>

          <div class="card chart-card">
            <div class="card-header" style="border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 16px; font-weight:600; font-size:14px; color:var(--text-primary)">
              ⚖ Open Fleet Size Distribution (DWT)
            </div>
            <div class="chart-container">
              <canvas id="chart-vessel-sizes"></canvas>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  async init() {
    this.destroyCharts();

    try {
      const data = await API._req('GET', '/analytics');
      if (!data) return;

      // Update KPI counts
      document.getElementById('kpi-total-emails').textContent = data.total_emails || 0;
      document.getElementById('kpi-tonnage').textContent = data.tonnage_records || 0;
      document.getElementById('kpi-cargo-vc').textContent = data.cargo_vc_records || 0;
      document.getElementById('kpi-cargo-tc').textContent = data.cargo_tc_records || 0;

      // Define Theme Colors (matching CSS variables)
      const colors = {
        gold: '#f0b429',
        blue: '#3d8bff',
        purple: '#a855f7',
        border: '#1a2540',
        text: '#8b9ab8',
        tooltipBg: '#0d1421'
      };

      const chartConfigDefaults = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: colors.text,
              font: { family: 'Inter', size: 12 }
            }
          },
          tooltip: {
            backgroundColor: colors.tooltipBg,
            titleColor: '#fff',
            bodyColor: colors.text,
            borderColor: colors.border,
            borderWidth: 1,
            titleFont: { family: 'Inter', weight: 'bold' },
            bodyFont: { family: 'Inter' }
          }
        },
        scales: {
          x: {
            grid: { color: colors.border },
            ticks: { color: colors.text, font: { family: 'Inter' } }
          },
          y: {
            grid: { color: colors.border },
            ticks: { color: colors.text, font: { family: 'Inter' }, precision: 0 }
          }
        }
      };

      // 1. Line Chart: Volume Trend
      const ctxTrend = document.getElementById('chart-volume-trend').getContext('2d');
      const chartTrend = new Chart(ctxTrend, {
        type: 'line',
        data: {
          labels: data.trend.labels.map(l => {
            const parts = l.split('-');
            if (parts.length === 3) {
              const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
              return `${parseInt(parts[2])} ${months[parseInt(parts[1]) - 1]}`;
            }
            return l;
          }),
          datasets: [
            {
              label: 'Tonnage',
              data: data.trend.series.tonnage,
              borderColor: colors.gold,
              backgroundColor: 'rgba(240, 180, 41, 0.1)',
              tension: 0.3,
              fill: true,
              borderWidth: 2
            },
            {
              label: 'Cargo VC',
              data: data.trend.series.cargo_vc,
              borderColor: colors.blue,
              backgroundColor: 'rgba(61, 139, 255, 0.1)',
              tension: 0.3,
              fill: true,
              borderWidth: 2
            },
            {
              label: 'Cargo TC',
              data: data.trend.series.cargo_tc,
              borderColor: colors.purple,
              backgroundColor: 'rgba(168, 85, 247, 0.1)',
              tension: 0.3,
              fill: true,
              borderWidth: 2
            }
          ]
        },
        options: {
          ...chartConfigDefaults,
          interaction: { mode: 'index', intersect: false }
        }
      });
      this._charts.push(chartTrend);

      // 2. Doughnut Chart: Category Distribution
      const ctxDist = document.getElementById('chart-category-dist').getContext('2d');
      const chartDist = new Chart(ctxDist, {
        type: 'doughnut',
        data: {
          labels: ['Tonnage', 'Cargo VC', 'Cargo TC'],
          datasets: [{
            data: [
              data.tonnage_records || 0,
              data.cargo_vc_records || 0,
              data.cargo_tc_records || 0
            ],
            backgroundColor: [colors.gold, colors.blue, colors.purple],
            borderWidth: 2,
            borderColor: '#111927'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: chartConfigDefaults.plugins,
          cutout: '70%'
        }
      });
      this._charts.push(chartDist);

      // 3. Horizontal Bar Chart: Top Ports
      const ctxPorts = document.getElementById('chart-top-ports').getContext('2d');
      const chartPorts = new Chart(ctxPorts, {
        type: 'bar',
        data: {
          labels: data.top_ports.labels,
          datasets: [{
            label: 'Cargo Openings',
            data: data.top_ports.data,
            backgroundColor: 'rgba(61, 139, 255, 0.75)',
            borderColor: colors.blue,
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          ...chartConfigDefaults,
          indexAxis: 'y',
          scales: {
            x: {
              grid: { color: colors.border },
              ticks: { color: colors.text, font: { family: 'Inter' }, precision: 0 }
            },
            y: {
              grid: { display: false },
              ticks: { color: colors.text, font: { family: 'Inter' } }
            }
          }
        }
      });
      this._charts.push(chartPorts);

      // 4. Vertical Bar Chart: Vessel Size distribution
      const ctxSizes = document.getElementById('chart-vessel-sizes').getContext('2d');
      const chartSizes = new Chart(ctxSizes, {
        type: 'bar',
        data: {
          labels: data.vessel_sizes.labels.map(l => l.split(' (')[0]),
          datasets: [{
            label: 'Open Vessels',
            data: data.vessel_sizes.data,
            backgroundColor: 'rgba(240, 180, 41, 0.75)',
            borderColor: colors.gold,
            borderWidth: 1,
            borderRadius: 4
          }]
        },
        options: {
          ...chartConfigDefaults,
          scales: {
            x: {
              grid: { display: false },
              ticks: { color: colors.text, font: { family: 'Inter' } }
            },
            y: {
              grid: { color: colors.border },
              ticks: { color: colors.text, font: { family: 'Inter' }, precision: 0 }
            }
          }
        }
      });
      this._charts.push(chartSizes);

    } catch (e) {
      Toast.show('Failed to load analytics: ' + e.message, 'error');
    }
  },

  destroyCharts() {
    if (this._charts && this._charts.length > 0) {
      this._charts.forEach(c => {
        if (c && typeof c.destroy === 'function') {
          c.destroy();
        }
      });
    }
    this._charts = [];
  }
};
