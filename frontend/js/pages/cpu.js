/**
 * CPU Page Controller.
 */

class CPUPage {
  constructor() {
    this.chart = null;
  }

  init() {
    this.chart = new MiniChart('cpu-detailed-canvas', {
      color: '#06b6d4',
      unit: '%',
      maxY: 100,
      maxPoints: 60
    });

    window.addEventListener('telemetry-update', (e) => this.update(e.detail));
    this.fetchWorkloadAnalysis();
    setInterval(() => {
      if (window.app && window.app.currentPage === 'cpu') {
        this.fetchWorkloadAnalysis();
      }
    }, 6000);

    const btnOpt = document.getElementById('btn-optimize-cpu');
    if (btnOpt) {
      btnOpt.addEventListener('click', async () => {
        btnOpt.disabled = true;
        const originalHtml = btnOpt.innerHTML;
        btnOpt.innerHTML = '<span>⚡ Mengoptimalkan...</span>';

        if (window.showToast) {
          window.showToast('info', 'Mengevaluasi beban prosesor & menstabilkan CPU...', 'CPU Optimizer', 2500);
        }

        try {
          const res = await fetch('/api/dahoo/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              action_type: 'OPTIMIZE_CPU',
              session_id: window.dahoo ? window.dahoo.sessionId : 'default',
              confirmed: true
            })
          });

          if (res.ok) {
            const data = await res.json();
            if (data.success) {
              const vDetail = data.verification?.detail ? ` • ${data.verification.detail}` : '';
              if (window.showToast) {
                window.showToast('success', `${data.message}${vDetail}`, 'CPU Optimizer Berhasil', 5000);
              }
            } else if (data.is_protected) {
              if (window.showToast) {
                window.showToast('warning', `${data.message}. ${data.recommendation || ''}`, 'Proses Terproteksi', 5000);
              }
            } else {
              if (window.showToast) {
                window.showToast('danger', data.message || 'Optimasi CPU tidak berhasil.', 'CPU Optimizer Gagal', 4500);
              }
            }
          } else {
            if (window.showToast) {
              window.showToast('danger', 'Gagal menghubungi service optimasi CPU.', 'CPU Optimizer Gagal', 4500);
            }
          }
        } catch (err) {
          if (window.showToast) {
            window.showToast('danger', `Kendala: ${err.message}`, 'CPU Optimizer', 3000);
          }
        } finally {
          btnOpt.disabled = false;
          btnOpt.innerHTML = originalHtml;
        }
      });
    }

    const btnAskDahooCpu = document.getElementById('btn-ask-dahoo-cpu');
    if (btnAskDahooCpu) {
      btnAskDahooCpu.addEventListener('click', () => {
        if (window.dahoo) {
          window.dahoo.askContextual('Tolong analisis kondisi prosesor dan beban kerja CPU saat ini.');
        }
      });
    }
  }

  update(snap) {
    if (!snap || !snap.cpu) return;
    const cpu = snap.cpu;

    // Header values
    document.getElementById('cpu-brand-name').textContent = cpu.processor_name || 'Windows Processor';
    document.getElementById('cpu-cores-text').textContent = `${cpu.physical_cores} Physical / ${cpu.logical_cores} Logical Cores`;
    document.getElementById('cpu-freq-text').textContent = `${cpu.frequency?.current_mhz || 0} MHz`;
    document.getElementById('cpu-total-perc').textContent = `${cpu.total_percent}%`;

    if (this.chart) this.chart.push(cpu.total_percent);

    // Per Core Matrix
    const coreGrid = document.getElementById('cpu-cores-grid');
    if (coreGrid && cpu.per_core) {
      coreGrid.innerHTML = cpu.per_core.map((perc, idx) => `
        <div class="card" style="padding: 0.75rem;">
          <div style="display: flex; justify-content: space-between; font-size: 0.75rem; margin-bottom: 0.35rem;">
            <span class="text-secondary font-mono">Core ${idx}</span>
            <span class="font-mono ${perc > 80 ? 'text-rose' : 'text-cyan'}">${perc}%</span>
          </div>
          <div class="progress-container" style="height: 4px;">
            <div class="progress-bar ${perc > 80 ? 'critical' : perc > 60 ? 'warning' : ''}" style="width: ${perc}%;"></div>
          </div>
        </div>
      `).join('');
    }
  }

  async fetchWorkloadAnalysis() {
    try {
      const res = await fetch('/api/analysis/cpu_workload');
      if (res.ok) {
        const data = await res.json();
        const elAnalysis = document.getElementById('cpu-analysis-summary');
        const elRec = document.getElementById('cpu-analysis-rec');
        const elContrib = document.getElementById('cpu-analysis-contrib');
        const elBaseline = document.getElementById('cpu-analysis-baseline');

        if (elAnalysis) elAnalysis.textContent = data.analysis;
        if (elRec) elRec.textContent = data.recommendation;
        if (elContrib) elContrib.textContent = `${data.primary_contributor} (${data.contributor_cpu}%)`;
        if (elBaseline) elBaseline.textContent = data.baseline;
      }
    } catch (e) {}
  }
}

window.cpuPage = new CPUPage();
