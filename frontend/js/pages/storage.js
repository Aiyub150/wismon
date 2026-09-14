/**
 * Storage Page Controller & Storage Analyzer with Safe Review Mode.
 * Supports hardware model identification, multi-drive scanning, and safe recycling.
 */

class StoragePage {
  constructor() {
    this.ioChart = null;
    this.knownDrives = [];
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

    // Update target drive selector options if drive list changed
    const targetSelect = document.getElementById('storage-scan-target');
    if (targetSelect && drives.length > 0) {
      const driveMounts = drives.map(d => d.device || d.mountpoint).sort().join(',');
      if (this._lastDrivesStr !== driveMounts) {
        this._lastDrivesStr = driveMounts;
        const currentVal = targetSelect.value;
        let html = '<option value="">Semua Drive (All)</option>';
        drives.forEach(d => {
          const mount = d.device || d.mountpoint;
          const label = `${mount} (${d.category || 'Drive'} - ${d.model ? d.model.substring(0, 20) : (d.volume_name || d.fstype)})`;
          html += `<option value="${mount}">${escapeHtml(label)}</option>`;
        });
        targetSelect.innerHTML = html;
        if (currentVal) targetSelect.value = currentVal;
      }
    }

    // 1. Render Drives with Hardware Info
    const driveGrid = document.getElementById('storage-drives-grid');
    if (driveGrid) {
      driveGrid.innerHTML = drives.map(d => {
        const mount = d.device || d.mountpoint;
        const model = d.model || 'Standard Storage Device';
        const busType = d.bus_type && d.bus_type !== 'Unknown' ? d.bus_type : '';
        const category = d.category || 'Disk Volume';
        const freeGb = (d.free_bytes / (1024**3)).toFixed(1);
        const totalGb = (d.total_bytes / (1024**3)).toFixed(1);
        const volName = d.volume_name ? `• "${d.volume_name}"` : '';

        // Category badge color
        let catBadgeClass = 'badge-neutral';
        if (category.includes('SSD') || busType === 'NVMe') catBadgeClass = 'badge-primary';
        else if (category.includes('USB')) catBadgeClass = 'badge-warning';
        else if (category.includes('SD')) catBadgeClass = 'badge-info';

        return `
          <div class="card" style="padding: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem;">
              <div style="display: flex; align-items: center; gap: 0.6rem;">
                <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-primary">
                  <line x1="22" x2="2" y1="12" y2="12"/>
                  <path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
                  <line x1="6" x2="6.01" y1="16" y2="16"/>
                  <line x1="10" x2="10.01" y1="16" y2="16"/>
                </svg>
                <div>
                  <div style="display: flex; align-items: center; gap: 0.4rem;">
                    <strong style="font-size: 1rem;">Drive ${escapeHtml(mount)}</strong>
                    <span class="badge ${catBadgeClass} font-mono" style="font-size: 0.65rem; padding: 0.15rem 0.4rem;">${category}</span>
                  </div>
                  <div class="text-muted" style="font-size: 0.72rem; line-height: 1.2; margin-top: 0.2rem;" title="${escapeHtml(model)}">
                    ${escapeHtml(model)} ${busType ? `(${busType})` : ''} ${volName}
                  </div>
                </div>
              </div>
              <span class="badge ${d.percent > 90 ? 'badge-critical' : d.percent > 75 ? 'badge-warning' : 'badge-healthy'} font-mono">${d.percent}%</span>
            </div>

            <div class="progress-container" style="height: 6px; margin: 0.6rem 0 0.5rem 0;">
              <div class="progress-bar ${d.percent > 90 ? 'critical' : d.percent > 75 ? 'warning' : ''}" style="width: ${d.percent}%;"></div>
            </div>

            <div style="display: flex; justify-content: space-between; font-size: 0.75rem;" class="text-secondary font-mono">
              <span>Free: <strong class="text-foreground">${freeGb} GB</strong></span>
              <span>Total: ${totalGb} GB (${d.fstype})</span>
            </div>
          </div>
        `;
      }).join('');
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
    const targetSelect = document.getElementById('storage-scan-target');
    const targetDrive = targetSelect ? targetSelect.value : '';

    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="spinner-border spinner-border-sm" style="margin-right: 6px;"></span> Scanning ${targetDrive ? targetDrive : 'All Drives'}...`;
    }

    try {
      const res = await fetch('/api/analysis/storage/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_drive: targetDrive || null })
      });

      if (res.ok) {
        const data = await res.json();
        this.renderScanResults(data);
      } else {
        const err = await res.json();
        if (window.showToast) {
          window.showToast('danger', err.detail || 'Scan failed', 'Storage Analyzer');
        }
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
        btn.innerHTML = `
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px;"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          Scan Storage Analyzer
        `;
      }
    }
  }

  renderScanResults(data) {
    const box = document.getElementById('storage-analyzer-results');
    if (!box) return;
    box.style.display = 'block';

    const temp = data.temp_cleanup || {};
    const junkFolders = data.junk_folders || [];
    const largeFiles = data.large_files || [];

    const targetBadge = document.getElementById('analyzer-target-badge');
    if (targetBadge) {
      targetBadge.textContent = `Target: ${data.target_drive || 'All Drives'}`;
    }

    const tempMb = document.getElementById('analyzer-temp-mb');
    const tempCount = document.getElementById('analyzer-temp-count');
    const reclaim = document.getElementById('analyzer-reclaimable');

    if (tempMb) tempMb.textContent = `${temp.total_mb || 0} MB`;
    if (tempCount) tempCount.textContent = `${temp.file_count || 0} files in Temp`;
    if (reclaim) reclaim.textContent = `${data.total_reclaimable_estimate_mb || 0} MB`;

    // 1. Junk Folders Table
    const junkTbody = document.getElementById('analyzer-junk-folders-tbody');
    if (junkTbody) {
      if (junkFolders.length > 0) {
        junkTbody.innerHTML = junkFolders.slice(0, 20).map(f => {
          const encodedPath = encodeURIComponent(f.path);
          return `
            <tr>
              <td>
                <div style="font-weight: 600; display: flex; align-items: center; gap: 0.4rem;">
                  <span>📁</span>
                  <span>${escapeHtml(f.name)}</span>
                </div>
                <div class="text-muted font-mono" style="font-size: 0.65rem; word-break: break-all;">${escapeHtml(f.path)}</div>
              </td>
              <td class="font-mono text-warning font-semibold">~${f.estimated_mb} MB</td>
              <td><span class="badge badge-warning font-mono">${escapeHtml(f.type || 'Cache Folder')}</span></td>
              <td style="text-align: right;">
                <button class="btn btn-secondary btn-sm" style="color: #EF4444; border-color: rgba(239, 68, 68, 0.4);" onclick="storagePage.deleteFolder('${encodedPath}', '${escapeHtml(f.name)}', ${f.estimated_mb})">
                  🗑️ Recycle Folder
                </button>
              </td>
            </tr>
          `;
        }).join('');
      } else {
        junkTbody.innerHTML = '<tr><td colspan="4" class="text-muted text-center" style="padding: 1.5rem;">Tidak ditemukan folder sampah atau cache besar (> 20 MB) pada drive yang dipindai.</td></tr>';
      }
    }

    // 2. Large files table with Safe Recycle Bin Action
    const largeTbody = document.getElementById('analyzer-large-files-tbody');
    if (largeTbody) {
      if (largeFiles.length > 0) {
        largeTbody.innerHTML = largeFiles.slice(0, 15).map(f => {
          const encodedPath = encodeURIComponent(f.path);
          return `
            <tr>
              <td>
                <div style="font-weight: 600; display: flex; align-items: center; gap: 0.4rem;">
                  <span>📄</span>
                  <span>${escapeHtml(f.name)}</span>
                </div>
                <div class="text-muted font-mono" style="font-size: 0.65rem; word-break: break-all;">${escapeHtml(f.path)}</div>
              </td>
              <td class="font-mono text-cyan">${f.size_mb} MB</td>
              <td><span class="badge badge-info font-mono">Large File</span></td>
              <td style="text-align: right;">
                <button class="btn btn-secondary btn-sm" style="color: #EF4444; border-color: rgba(239, 68, 68, 0.4);" onclick="storagePage.deleteFile('${encodedPath}', '${escapeHtml(f.name)}')">
                  🗑️ Recycle File
                </button>
              </td>
            </tr>
          `;
        }).join('');
      } else {
        largeTbody.innerHTML = '<tr><td colspan="4" class="text-muted text-center" style="padding: 1.5rem;">Tidak ditemukan file berukuran > 100 MB pada direktori yang dipindai.</td></tr>';
      }
    }
  }

  deleteFolder(encodedPath, folderName, sizeMb) {
    const targetPath = decodeURIComponent(encodedPath);
    const confirmMsg = `Pindahkan folder sampah/cache '${folderName}' (~${sizeMb} MB) ke Windows Recycle Bin?\n\nFolder ini dapat dipulihkan kembali dari Recycle Bin jika sewaktu-waktu masih diperlukan.`;

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
            window.showToast('success', data.message || `Folder '${folderName}' berhasil dipindahkan ke Recycle Bin.`, 'Ruang Disk Dibersihkan');
          }
          this.runStorageScan();
        } else {
          if (window.showToast) {
            window.showToast('danger', data.error || 'Gagal memindahkan folder ke Recycle Bin.', 'Gagal Hapus');
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
        'Pindahkan Folder ke Recycle Bin',
        confirmMsg,
        executeDelete,
        'Pindahkan ke Recycle Bin',
        'Batal',
        'warning'
      );
    } else {
      if (confirm(confirmMsg)) {
        executeDelete();
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

