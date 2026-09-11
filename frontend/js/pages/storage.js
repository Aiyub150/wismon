/**
 * Storage Page Controller & Storage Analyzer.
 */

class StoragePage {
  constructor() {
    this.ioChart = null;
  }

  init() {
    this.ioChart = new MiniChart('storage-io-canvas', {
      color: '#10b981',
      unit: 'MB/s',
      autoScaleY: true,
      maxPoints: 60
    });

    window.addEventListener('telemetry-update', (e) => this.update(e.detail));

    const scanBtn = document.getElementById('run-storage-scan-btn');
    if (scanBtn) {
      scanBtn.addEventListener('click', () => this.runStorageScan());
    }
  }

  update(snap) {
    if (!snap || !snap.storage) return;
    const stor = snap.storage;
    const drives = stor.drives || [];
    const io = stor.io || {};

    // 1. Render Drives
    const driveGrid = document.getElementById('storage-drives-grid');
    if (driveGrid) {
      driveGrid.innerHTML = drives.map(d => `
        <div class="card">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="font-size: 1.2rem;">💾</span>
              <div>
                <strong style="font-size: 0.95rem;">Drive ${d.device || d.mountpoint}</strong>
                <div class="text-muted" style="font-size: 0.7rem;">${d.fstype}</div>
              </div>
            </div>
            <span class="badge ${d.percent > 90 ? 'badge-critical' : d.percent > 75 ? 'badge-warning' : 'badge-healthy'}">${d.percent}%</span>
          </div>
          <div class="progress-container" style="height: 6px; margin-bottom: 0.5rem;">
            <div class="progress-bar ${d.percent > 90 ? 'critical' : d.percent > 75 ? 'warning' : ''}" style="width: ${d.percent}%;"></div>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 0.75rem;" class="text-secondary font-mono">
            <span>Free: ${(d.free_bytes / (1024**3)).toFixed(1)} GB</span>
            <span>Total: ${(d.total_bytes / (1024**3)).toFixed(1)} GB</span>
          </div>
        </div>
      `).join('');
    }

    // 2. Render Live I/O
    const readMb = (io.read_bytes_sec / (1024**2)).toFixed(2);
    const writeMb = (io.write_bytes_sec / (1024**2)).toFixed(2);
    const readOps = io.read_ops_sec || 0;
    const writeOps = io.write_ops_sec || 0;

    document.getElementById('disk-read-speed').textContent = `${readMb} MB/s`;
    document.getElementById('disk-write-speed').textContent = `${writeMb} MB/s`;
    document.getElementById('disk-read-ops').textContent = `${readOps}/s`;
    document.getElementById('disk-write-ops').textContent = `${writeOps}/s`;

    if (this.ioChart) {
      const totalMb = parseFloat(readMb) + parseFloat(writeMb);
      this.ioChart.push(totalMb);
    }
  }

  async runStorageScan() {
    const btn = document.getElementById('run-storage-scan-btn');
    const resultBox = document.getElementById('storage-analyzer-results');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Scanning Storage...';
    }

    try {
      const res = await fetch('/api/analysis/storage/scan', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        this.renderScanResults(data);
      }
    } catch (e) {
      alert('Error performing storage scan: ' + e.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Run Storage Analyzer Scan';
      }
    }
  }

  renderScanResults(data) {
    const box = document.getElementById('storage-analyzer-results');
    if (!box) return;
    box.style.display = 'block';

    const temp = data.temp_cleanup || {};
    const largeFiles = data.large_files || [];
    const oldFiles = data.old_files || [];

    document.getElementById('analyzer-temp-mb').textContent = `${temp.total_mb || 0} MB`;
    document.getElementById('analyzer-temp-count').textContent = `${temp.file_count || 0} files in Temp`;
    document.getElementById('analyzer-reclaimable').textContent = `${data.total_reclaimable_estimate_mb || 0} MB`;

    // Large files list
    const largeTbody = document.getElementById('analyzer-large-files-tbody');
    if (largeTbody) {
      largeTbody.innerHTML = largeFiles.slice(0, 10).map(f => `
        <tr>
          <td><strong>${escapeHtml(f.name)}</strong><br><span class="text-muted font-mono" style="font-size: 0.65rem;">${escapeHtml(f.path)}</span></td>
          <td class="font-mono text-cyan">${f.size_mb} MB</td>
          <td><span class="badge badge-info">Large File</span></td>
        </tr>
      `).join('') || '<tr><td colspan="3" class="text-muted text-center">No files > 100 MB found in scanned user directories.</td></tr>';
    }
  }
}

window.storagePage = new StoragePage();
