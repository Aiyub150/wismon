/**
 * Memory Page Controller.
 */

class MemoryPage {
  constructor() {
    this.chart = null;
  }

  init() {
    this.chart = new MiniChart('mem-detailed-canvas', {
      color: '#6366f1',
      unit: '%',
      maxY: 100
    });

    window.addEventListener('telemetry-update', (e) => this.update(e.detail));

    const btnOptRam = document.getElementById('btn-optimize-ram');
    if (btnOptRam) {
      btnOptRam.addEventListener('click', async () => {
        btnOptRam.disabled = true;
        const originalHtml = btnOptRam.innerHTML;
        btnOptRam.innerHTML = '<span>⚡ Mengoptimalkan...</span>';

        if (window.showToast) {
          window.showToast('info', 'Membersihkan working set RAM via Windows EmptyWorkingSet...', 'Memory Optimizer', 2500);
        }

        try {
          const res = await fetch('/api/dahoo/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              action_type: 'TRIM_MEMORY',
              session_id: window.dahoo ? window.dahoo.sessionId : 'default',
              confirmed: true
            })
          });

          if (res.ok) {
            const data = await res.json();
            if (data.success) {
              const vDetail = data.verification?.detail ? ` • ${data.verification.detail}` : '';
              if (window.showToast) {
                window.showToast('success', `${data.message}${vDetail}`, 'Optimasi Memori Berhasil', 5000);
              }
            } else {
              if (window.showToast) {
                window.showToast('danger', data.message || 'Pembersihan memori tidak dapat diselesaikan.', 'Optimasi Memori Gagal', 4500);
              }
            }
          } else {
            if (window.showToast) {
              window.showToast('danger', 'Gagal menghubungi service optimasi memori.', 'Optimasi Memori Gagal', 4500);
            }
          }
        } catch (err) {
          if (window.showToast) {
            window.showToast('danger', `Kendala: ${err.message}`, 'Memory Optimizer', 3000);
          }
        } finally {
          btnOptRam.disabled = false;
          btnOptRam.innerHTML = originalHtml;
        }
      });
    }

    const btnAskDahooRam = document.getElementById('btn-ask-dahoo-ram');
    if (btnAskDahooRam) {
      btnAskDahooRam.addEventListener('click', () => {
        if (window.dahoo) {
          window.dahoo.askContextual('Tolong analisis kondisi memori RAM, commit charge, dan kernel pool saat ini.');
        }
      });
    }
  }

  update(snap) {
    if (!snap || !snap.memory) return;
    const mem = snap.memory;
    const deep = mem.deep || {};

    // Basic Metrics
    const totalGb = (mem.total_bytes / (1024**3)).toFixed(1);
    const usedGb = (mem.used_bytes / (1024**3)).toFixed(1);
    const availGb = (mem.available_bytes / (1024**3)).toFixed(1);
    const freeGb = (mem.free_bytes / (1024**3)).toFixed(1);

    document.getElementById('mem-total-perc').textContent = `${mem.percent}%`;
    document.getElementById('mem-used-text').textContent = `${usedGb} GB`;
    document.getElementById('mem-available-text').textContent = `${availGb} GB`;
    document.getElementById('mem-free-text').textContent = `${freeGb} GB`;
    document.getElementById('mem-capacity-text').textContent = `${totalGb} GB Total`;

    if (this.chart) this.chart.push(mem.percent);

    // Deep Memory Metrics from Win32 GetPerformanceInfo
    const pagedMb = (deep.paged_pool / (1024**2)).toFixed(0);
    const nonpagedMb = (deep.nonpaged_pool / (1024**2)).toFixed(0);
    const commitChargeGb = (deep.commit_charge / (1024**3)).toFixed(1);
    const commitLimitGb = (deep.commit_limit / (1024**3)).toFixed(1);
    const cacheGb = (deep.system_cache / (1024**3)).toFixed(1);

    document.getElementById('mem-paged-pool').textContent = `${pagedMb} MB`;
    document.getElementById('mem-nonpaged-pool').textContent = `${nonpagedMb} MB`;
    document.getElementById('mem-commit-charge').textContent = `${commitChargeGb} / ${commitLimitGb} GB`;
    document.getElementById('mem-system-cache').textContent = `${cacheGb} GB`;
    document.getElementById('mem-handles-count').textContent = (deep.handle_count || 0).toLocaleString();

    // Commit ratio progress bar
    if (deep.commit_limit > 0) {
      const commitPerc = Math.min(100, Math.round((deep.commit_charge / deep.commit_limit) * 100));
      const commitBar = document.getElementById('mem-commit-bar');
      if (commitBar) commitBar.style.width = `${commitPerc}%`;
    }

    // Diagnostics
    const diagText = document.getElementById('mem-diagnostics-text');
    if (diagText) {
      if (mem.percent > 90) {
        diagText.innerHTML = `<span class="text-rose">CRITICAL: Severe memory pressure detected (${mem.percent}%). Processes are competing for page allocations. Inspect process working sets immediately.</span>`;
      } else if (mem.percent > 75) {
        diagText.innerHTML = `<span class="text-amber">WARNING: Memory utilization is elevated (${mem.percent}%). Monitor commit charge and potential memory leaks.</span>`;
      } else {
        diagText.innerHTML = `<span class="text-emerald">NORMAL: Memory pools and page allocations are operating within stable limits.</span>`;
      }
    }
  }
}

window.memoryPage = new MemoryPage();
