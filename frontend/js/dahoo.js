/**
 * Dahoo Assistant UI Controller.
 * Features an interactive Wolf Mascot with dynamic facial expressions,
 * session-aware conversational memory, WhatsApp-style bubbles, XSS protection,
 * and transparent AI mode routing (Gemini 3.5 Flash & Local Engine).
 */

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatMarkdown(text) {
  if (!text) return '';
  const escaped = escapeHtml(text);
  return escaped
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code style="padding: 2px 5px; background: rgba(0,0,0,0.06); border-radius: 4px; font-family: monospace; font-size: 0.85em;">$1</code>');
}

class DahooController {
  constructor() {
    this.avatarBtn = document.getElementById('dahoo-avatar');
    this.speechBubble = document.getElementById('dahoo-speech-bubble');
    this.drawer = document.getElementById('dahoo-drawer');
    this.closeBtn = document.getElementById('close-dahoo-btn');
    this.newSessionBtn = document.getElementById('new-dahoo-session-btn');
    this.chatBody = document.getElementById('dahoo-chat-body');
    this.chatInput = document.getElementById('dahoo-input');
    this.sendBtn = document.getElementById('dahoo-send-btn');
    this.modelBadge = document.getElementById('dahoo-model-badge');
    this.thinkingBadge = document.getElementById('dahoo-thinking-badge');
    this.costBadge = document.getElementById('dahoo-cost-badge');
    this.tokenBadge = document.getElementById('dahoo-tokens-badge');
    this.providerStatus = document.getElementById('dahoo-provider-status');
    this.fallbackHint = document.getElementById('dahoo-provider-fallback-hint');
    this.cloudAvailable = false;
    this.currentEmotion = 'normal';

    // Session Management (Multi-turn Memory)
    this.sessionId = localStorage.getItem('dahoo_session_id');
    if (!this.sessionId) {
      this.sessionId = 'sess_' + Math.random().toString(36).substring(2, 10);
      localStorage.setItem('dahoo_session_id', this.sessionId);
    }

    this.renderWolfAvatar('normal');
    this.initEvents();
    this.updateState();
    this.loadSessionHistory();
    setInterval(() => this.updateMetrics(), 15000);
  }

  renderWolfAvatar(emotion = 'normal') {
    if (!this.avatarBtn) return;
    this.currentEmotion = emotion;

    let eyeLeft = '<ellipse cx="15" cy="22" rx="2.5" ry="3.5" fill="#FFFFFF"/><circle cx="15.5" cy="21.5" r="1.5" fill="#1C2434"/>';
    let eyeRight = '<ellipse cx="29" cy="22" rx="2.5" ry="3.5" fill="#FFFFFF"/><circle cx="28.5" cy="21.5" r="1.5" fill="#1C2434"/>';
    let mouth = '<path d="M19 28 Q22 31 25 28" stroke="#1C2434" stroke-width="1.5" fill="none" stroke-linecap="round"/>';
    let extras = '';

    if (emotion === 'happy') {
      eyeLeft = '<path d="M12.5 22 Q15 19 17.5 22" stroke="#FFFFFF" stroke-width="2.5" fill="none" stroke-linecap="round"/>';
      eyeRight = '<path d="M26.5 22 Q29 19 31.5 22" stroke="#FFFFFF" stroke-width="2.5" fill="none" stroke-linecap="round"/>';
      mouth = '<path d="M18 27 Q22 33 26 27" stroke="#1C2434" stroke-width="1.8" fill="#F43F5E" stroke-linecap="round"/>';
    } else if (emotion === 'worried') {
      eyeLeft = '<ellipse cx="15" cy="23" rx="2" ry="3" fill="#FFFFFF"/><circle cx="15" cy="22.5" r="1.2" fill="#1C2434"/>';
      eyeRight = '<ellipse cx="29" cy="23" rx="2" ry="3" fill="#FFFFFF"/><circle cx="29" cy="22.5" r="1.2" fill="#1C2434"/>';
      mouth = '<path d="M19 30 Q22 27 25 30" stroke="#1C2434" stroke-width="1.5" fill="none" stroke-linecap="round"/>';
      extras = '<path d="M34 14 C34 12 36 9 36 9 C36 9 38 12 38 14 C38 15.5 36.8 16.5 35.5 16.5 C34.5 16.5 34 15.5 34 14 Z" fill="#38BDF8"/>';
    } else if (emotion === 'alert') {
      eyeLeft = '<ellipse cx="15" cy="22" rx="3" ry="4" fill="#FEE2E2"/><circle cx="15.5" cy="22" r="2" fill="#DC2626"/>';
      eyeRight = '<ellipse cx="29" cy="22" rx="3" ry="4" fill="#FEE2E2"/><circle cx="28.5" cy="22" r="2" fill="#DC2626"/>';
      mouth = '<circle cx="22" cy="29" r="2.5" fill="#1C2434"/>';
      extras = '<circle cx="37" cy="9" r="6" fill="#EF4444" stroke="#FFFFFF" stroke-width="1.5"/><text x="37" y="13" font-size="9" font-weight="bold" fill="#FFFFFF" text-anchor="middle">!</text>';
    }

    const wolfSvg = `
      <svg viewBox="0 0 44 44" class="wolf-svg">
        <polygon points="6,18 12,2 20,12" fill="#94A3B8"/>
        <polygon points="8,16 13,5 18,12" fill="#F472B6"/>
        <polygon points="38,18 32,2 24,12" fill="#94A3B8"/>
        <polygon points="36,16 31,5 26,12" fill="#F472B6"/>
        <path d="M10,14 Q22,9 34,14 Q41,25 36,36 Q22,43 8,36 Q3,25 10,14 Z" fill="#E2E8F0"/>
        <polygon points="3,25 10,23 7,29" fill="#CBD5E1"/>
        <polygon points="41,25 34,23 37,29" fill="#CBD5E1"/>
        <path d="M14,18 Q22,23 30,18 Q34,32 22,36 Q10,32 14,18 Z" fill="#FFFFFF"/>
        ${eyeLeft}
        ${eyeRight}
        <polygon points="20,24 24,24 22,27" fill="#1E293B"/>
        ${mouth}
        ${extras}
      </svg>
    `;

    this.avatarBtn.innerHTML = wolfSvg;
    const drawerAvatar = document.querySelector('.drawer-avatar');
    if (drawerAvatar) drawerAvatar.innerHTML = wolfSvg;
  }

  initEvents() {
    if (this.avatarBtn) this.avatarBtn.addEventListener('click', () => this.toggleDrawer());
    if (this.speechBubble) this.speechBubble.addEventListener('click', () => this.toggleDrawer());
    if (this.closeBtn) this.closeBtn.addEventListener('click', () => this.toggleDrawer(false));
    if (this.newSessionBtn) this.newSessionBtn.addEventListener('click', () => this.resetSession());
    if (this.sendBtn) this.sendBtn.addEventListener('click', () => this.sendMessage());
    if (this.chatInput) {
      this.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') this.sendMessage();
      });
    }

    const topbarDahoo = document.getElementById('topbar-dahoo-btn');
    if (topbarDahoo) topbarDahoo.addEventListener('click', () => this.toggleDrawer(true));

    document.querySelectorAll('.suggestion-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        if (this.chatInput) {
          this.chatInput.value = pill.textContent.trim();
          this.sendMessage();
        }
      });
    });


    window.addEventListener('telemetry-update', (e) => {
      const snap = e.detail;
      const score = snap.health ? snap.health.score : 100;
      const threatCount = snap.threats ? snap.threats.length : 0;
      const cpu = snap.cpu ? snap.cpu.total_percent : 0;
      this.setEmotion(score, threatCount, cpu);
      this.checkProactiveNotifications(snap);
    });
  }

  toggleDrawer(open) {
    if (!this.drawer) return;
    const shouldOpen = open !== undefined ? open : !this.drawer.classList.contains('open');
    if (shouldOpen) {
      this.drawer.classList.add('open');
      if (this.speechBubble) this.speechBubble.style.display = 'none';
      if (this.chatInput) this.chatInput.focus();
      this.updateMetrics();
    } else {
      this.drawer.classList.remove('open');
    }
  }

  setEmotion(score, threatCount, cpu) {
    if (!this.avatarBtn) return;
    let emotion = 'normal';
    if (threatCount > 0 || score < 40) emotion = 'alert';
    else if (cpu > 85 || score < 65) emotion = 'worried';
    else if (score >= 85) emotion = 'happy';

    this.avatarBtn.className = `dahoo-avatar-btn ${emotion}`;
    if (emotion !== this.currentEmotion) this.renderWolfAvatar(emotion);
  }

  async updateState() {
    try {
      const res = await fetch('/api/dahoo/state');
      if (res.ok) {
        const data = await res.json();
        if (this.speechBubble && data.proactive_speech) {
          this.speechBubble.textContent = data.proactive_speech;
        }
        this.cloudAvailable = data.cloud_available || false;
        const rawModel = data.active_model || (this.cloudAvailable ? 'Gemini 3.5 Flash' : 'Offline Rule Engine');
        // Clean any existing parenthesized suffix like (MEDIUM) to avoid duplicate (MEDIUM) (MEDIUM)
        const cleanModel = rawModel.replace(/\s*\([A-Za-z0-9_-]+\)\s*$/, '').trim();

        if (this.modelBadge) {
          this.modelBadge.textContent = data.provider_status || (this.cloudAvailable ? `● ${cleanModel} (Auto)` : '● Local Engine (Offline)');
        }
        if (this.thinkingBadge) {
          const lvl = data.thinking_level || 'medium';
          this.thinkingBadge.textContent = this.cloudAvailable ? `${cleanModel} (${lvl.toUpperCase()})` : 'Offline Rule Engine';
        }
        if (this.providerStatus) {
          this.providerStatus.innerHTML = this.cloudAvailable 
            ? `<span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10B981;"></span> <span>Auto: ${cleanModel}</span>`
            : `<span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #94A3B8;"></span> <span>Offline: Local Engine</span>`;
        }
        if (this.fallbackHint) {
          this.fallbackHint.textContent = this.cloudAvailable ? 'Auto-failover to Local Engine' : 'Zero API/Network overhead';
        }
      }
    } catch (e) {}
  }

  async updateMetrics() {
    try {
      const res = await fetch('/api/dahoo/metrics');
      if (res.ok) {
        const stats = await res.json();
        if (this.costBadge) this.costBadge.textContent = `$${stats.total_cost.toFixed(5)}`;
        if (this.tokenBadge) this.tokenBadge.textContent = stats.total_tokens.toLocaleString();
      }
    } catch (e) {}
  }

  async loadSessionHistory() {
    try {
      const res = await fetch(`/api/dahoo/history/${this.sessionId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
          if (this.chatBody) this.chatBody.innerHTML = '';
          for (const m of data.messages) {
            this.appendMessage(m.role, m.message, m.model || '', null, false);
          }
        }
      }
    } catch (e) {}
  }

  async resetSession() {
    try {
      await fetch(`/api/dahoo/history/${this.sessionId}`, { method: 'DELETE' });
    } catch (e) {}

    this.sessionId = 'sess_' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem('dahoo_session_id', this.sessionId);

    if (this.chatBody) {
      this.chatBody.innerHTML = `
        <div class="chat-msg assistant">
          <div class="chat-bubble">
            Aww! Sesi percakapan baru telah dimulai. 🐺<br><br>
            Aku membaca telemetry hardware aktual dan siap membantumu memahami kondisi komputer, mendiagnosis beban kerja, atau melakukan tindakan pemeliharaan sistem!
          </div>
          <span class="chat-meta"><span>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span> • Sesi Baru</span>
        </div>
      `;
    }

    if (window.showToast) {
      window.showToast('info', 'Sesi percakapan Dahoo telah di-reset.', 'Dahoo Memory', 2000);
    }
  }

  appendMessage(role, text, meta = '', action = null, scroll = true) {
    if (!this.chatBody) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${role}`;

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = formatMarkdown(text);

    // Render interactive Two-Phase Action Proposal Card
    if (action && action.type) {
      const actionBox = document.createElement('div');
      actionBox.className = 'chat-action-card';
      actionBox.style = 'margin-top: 0.75rem; padding: 0.6rem 0.75rem; border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.35); background: rgba(59, 130, 246, 0.06); font-size: 0.8rem;';

      const actionHeader = document.createElement('div');
      actionHeader.style = 'font-weight: 600; color: #2563EB; margin-bottom: 0.3rem; display: flex; align-items: center; gap: 4px;';
      actionHeader.innerHTML = `<span>⚡</span> <span>Rekomendasi Tindakan: <strong>${escapeHtml(action.label || 'Tindakan Sistem')}</strong></span>`;
      actionBox.appendChild(actionHeader);

      if (action.reason) {
        const reasonDiv = document.createElement('div');
        reasonDiv.style = 'color: var(--text-muted, #64748B); font-size: 0.75rem; margin-bottom: 0.4rem;';
        reasonDiv.innerHTML = `<em>Alasan:</em> ${escapeHtml(action.reason)}`;
        actionBox.appendChild(reasonDiv);
      }

      const btnRow = document.createElement('div');
      btnRow.style = 'display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.4rem;';

      const actBtn = document.createElement('button');
      actBtn.className = 'btn btn-primary btn-sm';
      actBtn.style = 'padding: 4px 12px; font-size: 0.78rem; font-weight: 600; display: flex; align-items: center; gap: 4px;';
      actBtn.innerHTML = `<span>✓</span> <span>Konfirmasi Tindakan</span>`;
      actBtn.onclick = () => {
        actBtn.disabled = true;
        actBtn.textContent = '⚡ Memproses...';
        if (window.showToast) {
          window.showToast('info', 'Mengeksekusi tindakan perbaikan sistem...', 'Dahoo Action Engine', 2500);
        }
        this.executeDahooAction(action.type, action.params, actionBox);
      };
      btnRow.appendChild(actBtn);

      const cancelBtn = document.createElement('button');
      cancelBtn.className = 'btn btn-secondary btn-sm';
      cancelBtn.style = 'padding: 4px 10px; font-size: 0.78rem;';
      cancelBtn.textContent = 'Batalkan';
      cancelBtn.onclick = () => {
        actionBox.remove();
        this.appendMessage('assistant', 'Tindakan dibatalkan. Hubungi aku lagi jika butuh bantuan! 🐺');
      };
      btnRow.appendChild(cancelBtn);

      actionBox.appendChild(btnRow);
      bubble.appendChild(actionBox);
    }

    msgDiv.appendChild(bubble);

    const metaSpan = document.createElement('span');
    metaSpan.className = 'chat-meta';
    if (role === 'user') {
      metaSpan.innerHTML = `<span>${timeStr}</span> <span style="color:#60A5FA;">✓✓</span>`;
    } else {
      metaSpan.innerHTML = `<span>${timeStr}</span> ${meta ? '• ' + escapeHtml(meta) : ''}`;
    }
    msgDiv.appendChild(metaSpan);

    this.chatBody.appendChild(msgDiv);
    if (scroll) this.chatBody.scrollTop = this.chatBody.scrollHeight;
  }

  async executeDahooAction(actionType, params = {}, actionBox = null) {
    this.showTypingIndicator();
    let progressTimer = null;
    const actBtn = actionBox ? actionBox.querySelector('button.btn-primary') : null;

    if (actBtn) {
      let step = 0;
      const steps = ['Validating target...', 'Executing action...', 'Verifying result...'];
      progressTimer = setInterval(() => {
        step = (step + 1) % steps.length;
        if (actBtn) actBtn.innerHTML = `⚡ <span>${steps[step]}</span>`;
      }, 1100);
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const res = await fetch('/api/dahoo/action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action_type: actionType,
          params: params,
          session_id: this.sessionId,
          confirmed: true
        }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (progressTimer) clearInterval(progressTimer);
      this.removeTypingIndicator();
      if (actionBox) actionBox.remove();

      if (res.ok) {
        const data = await res.json();
        const icon = data.success ? '✅' : '⚠️';
        let detailText = `${icon} **Laporan Tindakan Perbaikan:**\n\n${data.message || 'Tindakan berhasil dieksekusi.'}`;

        if (data.details && data.details.length > 0) {
          detailText += '\n\n**Rincian:**\n' + data.details.map(d => `• ${d}`).join('\n');
        }

        if (data.verification) {
          detailText += `\n\n📊 *Verifikasi Sistem:* ${data.verification.detail || 'Perubahan terpantau stabil.'}`;
        }

        this.appendMessage('assistant', detailText, 'Dahoo Action Engine');
        if (window.showToast) {
          window.showToast(data.success ? 'success' : 'warning', data.message || 'Tindakan selesai.', 'Dahoo Assistant');
        }

        window.dispatchEvent(new CustomEvent('threat-resolved', { detail: data }));
        this.updateState();
      } else {
        this.appendMessage('assistant', '⚠️ Gagal mengeksekusi tindakan perbaikan.', 'Dahoo Action Engine');
        if (window.showToast) {
          window.showToast('danger', 'Gagal mengeksekusi tindakan.', 'Dahoo Assistant');
        }
      }
    } catch (e) {
      if (progressTimer) clearInterval(progressTimer);
      this.removeTypingIndicator();
      if (actionBox) actionBox.remove();
      const isTimeout = e.name === 'AbortError';
      const errMsg = isTimeout ? 'Batas waktu respon 10 detik terlampaui (Timeout).' : e.message;
      this.appendMessage('assistant', `⚠️ Tindakan belum selesai: ${errMsg}\n\nSilakan coba kembali jika sistem belum merespons.`, 'Action Engine');
      if (window.showToast) {
        window.showToast('danger', 'Tindakan: ' + errMsg, 'Dahoo Assistant');
      }
    }
  }

  checkProactiveNotifications(snap) {
    if (!snap) return;
    const now = Date.now();
    if (!this._notifiedThreats) this._notifiedThreats = new Set();
    if (!this._lastAlertTime) this._lastAlertTime = 0;

    const threats = snap.threats || [];
    for (const t of threats) {
      if (!this._notifiedThreats.has(t.id)) {
        this._notifiedThreats.add(t.id);
        const action = t.pid
          ? { type: 'COOLDOWN_PROCESS', label: `Tangguhkan Proses ${t.target} (3.5s)`, reason: t.reason, params: { pid: t.pid, name: t.target } }
          : { type: 'RESOLVE_THREAT', label: 'Mitigasi Ancaman Ini', reason: t.reason, params: { threat_id: t.id } };

        this.appendMessage(
          'assistant',
          `🔔 **Peringatan Keamanan Sistem!**\n\nTerdeteksi anomali: **${t.category}** pada **${t.target}**.\n*Keterangan*: ${t.reason}\n\nApakah kamu ingin aku bantu menstabilkan anomali ini sekarang?`,
          'Proactive System Alert',
          action
        );

        if (this.speechBubble && !this.drawer.classList.contains('open')) {
          this.speechBubble.textContent = `Aww! Ada anomali keamanan: ${t.category}`;
          this.speechBubble.style.display = 'block';
        }
      }
    }

    const cpuVal = snap.cpu ? snap.cpu.total_percent : 0;
    if (cpuVal > 85 && (now - this._lastAlertTime > 90000)) {
      this._lastAlertTime = now;
      const topProc = snap.process?.top_cpu?.find(p => p.pid > 0 && !p.name.toLowerCase().includes('idle'));
      if (topProc && topProc.cpu_percent > 25) {
        const action = {
          type: 'COOLDOWN_PROCESS',
          label: `Tangguhkan ${topProc.name} (3.5s)`,
          reason: `Menyerap ${topProc.cpu_percent}% CPU`,
          params: { pid: topProc.pid, name: topProc.name }
        };
        this.appendMessage(
          'assistant',
          `🔔 **Peringatan Beban CPU Tinggi!**\n\nBeban CPU melonjak ke **${cpuVal}%**! Proses **${topProc.name}** (PID: ${topProc.pid}) menyerap **${topProc.cpu_percent}% CPU**.\n\nMau aku bantu menangguhkan proses ini selama 3.5 detik agar suhu dan CPU stabil kembali?`,
          'Proactive System Alert',
          action
        );

        if (this.speechBubble && !this.drawer.classList.contains('open')) {
          this.speechBubble.textContent = `CPU tinggi (${cpuVal}%) pada ${topProc.name}!`;
          this.speechBubble.style.display = 'block';
        }
      }
    }
  }

  showTypingIndicator() {
    if (!this.chatBody || document.getElementById('dahoo-typing-msg')) return;
    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-msg assistant';
    msgDiv.id = 'dahoo-typing-msg';

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    bubble.innerHTML = `
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    `;
    msgDiv.appendChild(bubble);
    this.chatBody.appendChild(msgDiv);
    this.chatBody.scrollTop = this.chatBody.scrollHeight;
  }

  removeTypingIndicator() {
    const typing = document.getElementById('dahoo-typing-msg');
    if (typing) typing.remove();
  }

  async sendMessage() {
    const text = this.chatInput.value.trim();
    if (!text) return;

    this.chatInput.value = '';
    this.appendMessage('user', text);
    this.showTypingIndicator();

    if (this.avatarBtn) this.avatarBtn.classList.add('thinking');

    try {
      const res = await fetch('/api/dahoo/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          session_id: this.sessionId
        })
      });

      this.removeTypingIndicator();

      if (res.ok) {
        const data = await res.json();
        const totalTok = (data.input_tokens || 0) + (data.output_tokens || 0);
        const metaText = data.engine === 'cloud' 
          ? `${data.model || 'Gemini 3.5 Flash'} (${totalTok} tok)`
          : 'Dahoo Local Engine';
        this.appendMessage('assistant', data.reply, metaText, data.action);
        this.updateMetrics();
      } else {
        this.appendMessage('assistant', 'Aww, maaf terjadi kendala saat memproses permintaanmu. Coba tanyakan kembali.');
      }
    } catch (err) {
      this.removeTypingIndicator();
      this.appendMessage('assistant', `Aww, server offline: ${err.message}`);
    } finally {
      if (this.avatarBtn) this.avatarBtn.classList.remove('thinking');
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.dahoo = new DahooController();
});

