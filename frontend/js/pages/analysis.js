/**
 * Analysis & Historical Data Page Controller.
 */

class AnalysisPage {
  constructor() {
    this.histChart = null;
  }

  init() {
    this.histChart = new MiniChart('analysis-history-canvas', {
      color: '#3C50E0',
      unit: '%',
      label: 'CPU Load',
      maxY: 100,
      maxPoints: 120
    });

    this.fetchBaselines();
    this.fetchHistory(3600);

    const rangeBtns = document.querySelectorAll('.history-range-btn');
    rangeBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        rangeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const sec = parseInt(btn.dataset.seconds, 10) || 3600;
        this.fetchHistory(sec);
      });
    });
  }

  async fetchBaselines() {
    try {
      const res = await fetch('/api/analysis/baseline');
      if (res.ok) {
        const data = await res.json();
        const cpu = data.cpu || {};
        const ram = data.ram || {};
        const net = data.network_mbps || {};

        const setVal = (id, val) => {
          const el = document.getElementById(id);
          if (el) el.textContent = val;
        };

        setVal('base-cpu-minmax', `${cpu.min || 0}–${cpu.max || 0}%`);
        setVal('base-cpu-avg', `${cpu.avg || 0}%`);

        setVal('base-ram-minmax', `${ram.min || 0}–${ram.max || 0}%`);
        setVal('base-ram-avg', `${ram.avg || 0}%`);

        setVal('base-net-minmax', `${net.min || 0}–${net.max || 0} Mbps`);
        setVal('base-net-avg', `${net.avg || 0} Mbps`);
      }
    } catch (e) {}
  }

  async fetchHistory(seconds) {
    const emptyNotice = document.getElementById('hist-empty-notice');
    try {
      const res = await fetch(`/api/analysis/history?seconds=${seconds}`);
      if (res.ok) {
        const records = await res.json();
        if (this.histChart) {
          if (records.length > 0) {
            this.histChart.dataPoints = records.map(r => ({
              val: r.cpu_percent,
              timeStr: new Date(r.timestamp * 1000).toLocaleTimeString('en-GB'),
              timestamp: r.timestamp * 1000
            }));
            this.histChart.resize();
            this.histChart.render();
            if (emptyNotice) emptyNotice.style.display = 'none';
          } else {
            if (emptyNotice) emptyNotice.style.display = 'block';
          }
        }

        // Summary stats for period
        if (records.length > 0) {
          const cpus = records.map(r => r.cpu_percent);
          const rams = records.map(r => r.ram_percent);
          const avgCpu = (cpus.reduce((a, b) => a + b, 0) / cpus.length).toFixed(1);
          const avgRam = (rams.reduce((a, b) => a + b, 0) / rams.length).toFixed(1);

          const elCpu = document.getElementById('hist-avg-cpu');
          const elRam = document.getElementById('hist-avg-ram');
          const elCount = document.getElementById('hist-samples-count');

          if (elCpu) elCpu.textContent = `${avgCpu}%`;
          if (elRam) elRam.textContent = `${avgRam}%`;
          if (elCount) elCount.textContent = `${records.length} samples`;
        }
      }
    } catch (e) {}
  }
}

window.analysisPage = new AnalysisPage();
