/**
 * Analysis & Historical Data Page Controller.
 */

class AnalysisPage {
  constructor() {
    this.histChart = null;
  }

  init() {
    this.histChart = new MiniChart('analysis-history-canvas', {
      color: '#06b6d4',
      unit: '%',
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
        const sec = parseInt(btn.dataset.seconds, 10);
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

        document.getElementById('base-cpu-minmax').textContent = `${cpu.min}–${cpu.max}%`;
        document.getElementById('base-cpu-avg').textContent = `${cpu.avg}%`;

        document.getElementById('base-ram-minmax').textContent = `${ram.min}–${ram.max}%`;
        document.getElementById('base-ram-avg').textContent = `${ram.avg}%`;

        document.getElementById('base-net-minmax').textContent = `${net.min}–${net.max} Mbps`;
        document.getElementById('base-net-avg').textContent = `${net.avg} Mbps`;
      }
    } catch (e) {}
  }

  async fetchHistory(seconds) {
    try {
      const res = await fetch(`/api/analysis/history?seconds=${seconds}`);
      if (res.ok) {
        const records = await res.json();
        if (this.histChart && records.length > 0) {
          this.histChart.dataPoints = records.map(r => r.cpu_percent);
          this.histChart.render();
        }

        // Summary stats for period
        if (records.length > 0) {
          const cpus = records.map(r => r.cpu_percent);
          const rams = records.map(r => r.ram_percent);
          const avgCpu = (cpus.reduce((a, b) => a + b, 0) / cpus.length).toFixed(1);
          const avgRam = (rams.reduce((a, b) => a + b, 0) / rams.length).toFixed(1);

          document.getElementById('hist-avg-cpu').textContent = `${avgCpu}%`;
          document.getElementById('hist-avg-ram').textContent = `${avgRam}%`;
          document.getElementById('hist-samples-count').textContent = records.length;
        }
      }
    } catch (e) {}
  }
}

window.analysisPage = new AnalysisPage();
