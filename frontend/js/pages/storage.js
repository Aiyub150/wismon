/**
 * Storage Page Controller & Storage Analyzer with Safe Review Mode.
 */

class StoragePage {
  constructor() {
    this.ioChart = null;
  }

  init() {
    this.ioChart = new MiniChart('storage-io-canvas', {
      color: '#10B981',
      unit: ' MB/s',
      label: 'Throughput',
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
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-primary">
                <line x1="22" x2="2" y1="12" y2="12"/>
                <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
                <line x1="6" x2="6.01" y1="16" y2="16"/>
                <line x1="10" x2="10.01" y1="16" y2="16"/>
              </svg>
              <div>
                <strong style="font-size: 0.95rem;">Drive ${escapeHtml(d.device || d.mountpoint)}</strong>
                <div class="text-muted" style="font-size: 0.7rem;">${d.fstype} • ${d.opts}</div>
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

    const readElem = document.getElementById('disk-read-speed');
    const writeElem = document.getElementById('disk-write-speed');
    const readOpsElem = document.getElementById('disk-read-ops');
    const writeOpsElem = document.getElementById('disk-write-ops');

    if (readElem) readElem.textContent = `${readMb} MB/s`;
    if (writeElem) writeElem.textContent = `${writeMb} MB/s`;
    if (readOpsElem) readOpsElem.textContent = `${readOps}/s`;
    if (writeOpsElem) writeOpsElem.textContent = `${writeOps}/s`;

    if (this.ioChart) {
      const totalMb = parseFloat((parseFloat(readMb) + parseFloat(writeMb)).toFixed(2));
      const timeStr = snap.timestamp ? new Date(snap.timestamp * 1000).toLocaleTimeString('en-GB') : null;
      this.ioChart.push(totalMb, timeStr);
    }
  }

  async runStorageScan() {
    const btn = document.getElementById('run-storage-scan-btn');
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
      if (window.showToast) {
        window.showToast('danger', 'Error memindai penyimpanan: ' + e.message, 'Storage Analyzer');
      } else {
        console.error('Error performing storage scan:', e);
      }
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

    const tempMb = document.getElementById('analyzer-temp-mb');
    const tempCount = document.getElementById('analyzer-temp-count');
    const reclaim = document.getElementById('analyzer-reclaimable');

    if (tempMb) tempMb.textContent = `${temp.total_mb || 0} MB`;
    if (tempCount) tempCount.textContent = `${temp.file_count || 0} files in Temp`;
    if (reclaim) reclaim.textContent = `${data.total_reclaimable_estimate_mb || 0} MB`;

    // Large files table with Safe Recycle Bin Action
    const largeTbody = document.getElementById('analyzer-large-files-tbody');
    if (largeTbody) {
      if (largeFiles.length > 0) {
        largeTbody.innerHTML = largeFiles.slice(0, 15).map(f => {
          const encodedPath = encodeURIComponent(f.path);
          return `
            <tr>
              <td>
                <div style="font-weight: 600;">${escapeHtml(f.name)}</div>
                <div class="text-muted font-mono" style="font-size: 0.65rem; word-break: break-all;">${escapeHtml(f.path)}</div>
              </td>
              <td class="font-mono text-cyan">${f.size_mb} MB</td>
              <td><span class="badge badge-info font-mono">Large File</span></td>
              <td style="text-align: right;">
                <button class="btn btn-secondary btn-sm" style="color: #EF4444; border-color: rgba(239, 68, 68, 0.4);" onclick="storagePage.deleteFile('${encodedPath}', '${escapeHtml(f.name)}')">
                  🗑️ Recycle
                </button>
              </td>
            </tr>
          `;
        }).join('');
      } else {
        largeTbody.innerHTML = '<tr><td colspan="4" class="text-muted text-center">No files > 100 MB found in scanned user directories.</td></tr>';
      }
    }
  }

  deleteFile(encodedPath, filename) {
    const targetPath = decodeURIComponent(encodedPath);
    const confirmMsg = `Pindahkan file '${filename}' ke Windows Recycle Bin?\n\nFile dapat dipulihkan kembali dari Recycle Bin jika sewaktu-waktu masih diperlukan.`;

    const executeDelete = async () => {
      try {
        const res = await fetch('/api/analysis/storage/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ filepath: targetPath })
        });

        const data = await res.json();
        if (data.success) {
          if (window.showToast) {
            window.showToast('success', data.message || 'File berhasil dipindahkan ke Recycle Bin.', 'Penyimpanan Lebih Lega');
          }
          this.runStorageScan();
        } else {
          if (window.showToast) {
            window.showToast('danger', data.error || 'Gagal memindahkan file ke Recycle Bin.', 'Penghapusan Gagal');
          }
        }
      } catch (e) {
        if (window.showToast) {
          window.showToast('danger', 'Gagal menghubungi server: ' + e.message, 'Koneksi Terputus');
        }
      }
    };

    if (window.showConfirm) {
      window.showConfirm(
        'Pindahkan ke Recycle Bin',
        confirmMsg,
        executeDelete,
        'Pindahkan',
        'Batal',
        'warning'
      );
    } else {
      if (confirm(confirmMsg)) {
        executeDelete();
      }
    }
  }
}

window.storagePage = new StoragePage();
