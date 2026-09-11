/**
 * Lightweight Real-Time HTML5 Canvas Time-Series Chart Engine.
 * Supports multi-series, gradient fills, gridlines, auto-scaling, and smooth updates.
 */

class MiniChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.options = Object.assign({
      maxPoints: 60,
      minY: 0,
      maxY: 100,
      autoScaleY: false,
      color: '#06b6d4',
      gradientFill: true,
      unit: '%',
      label: 'Value'
    }, options);

    this.dataPoints = [];
    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width = rect.width * dpr;
    this.canvas.height = (rect.height || 180) * dpr;
    this.ctx.scale(dpr, dpr);
    this.width = rect.width;
    this.height = rect.height || 180;
    this.render();
  }

  push(value) {
    if (value === null || value === undefined) value = 0;
    this.dataPoints.push(value);
    if (this.dataPoints.length > this.options.maxPoints) {
      this.dataPoints.shift();
    }
    this.render();
  }

  render() {
    if (!this.ctx || !this.width || !this.height) return;
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    const padTop = 15;
    const padBottom = 20;
    const chartHeight = h - padTop - padBottom;

    ctx.clearRect(0, 0, w, h);

    // Calculate Y limits
    let minY = this.options.minY;
    let maxY = this.options.maxY;
    if (this.options.autoScaleY && this.dataPoints.length > 0) {
      const maxVal = Math.max(...this.dataPoints);
      maxY = Math.max(maxVal * 1.2, 10);
    }

    // Draw Subtle Horizontal Gridlines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    const gridSteps = 4;
    for (let i = 0; i <= gridSteps; i++) {
      const y = padTop + (chartHeight / gridSteps) * i;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();

      // Axis label
      const val = Math.round(maxY - ((maxY - minY) / gridSteps) * i);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.25)';
      ctx.font = '10px monospace';
      ctx.fillText(`${val}${this.options.unit}`, 6, y - 3);
    }

    if (this.dataPoints.length < 2) return;

    // Calculate points
    const step = w / (this.options.maxPoints - 1);
    const startX = w - (this.dataPoints.length - 1) * step;

    const points = this.dataPoints.map((val, idx) => {
      const norm = Math.max(0, Math.min(1, (val - minY) / (maxY - minY || 1)));
      const x = startX + idx * step;
      const y = padTop + chartHeight * (1 - norm);
      return { x, y };
    });

    // Draw Area Fill
    if (this.options.gradientFill) {
      const grad = ctx.createLinearGradient(0, padTop, 0, h - padBottom);
      grad.addColorStop(0, this.hexToRgba(this.options.color, 0.35));
      grad.addColorStop(1, this.hexToRgba(this.options.color, 0.0));

      ctx.beginPath();
      ctx.moveTo(points[0].x, h - padBottom);
      ctx.lineTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        const xc = (points[i - 1].x + points[i].x) / 2;
        const yc = (points[i - 1].y + points[i].y) / 2;
        ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xc, yc);
      }
      ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
      ctx.lineTo(points[points.length - 1].x, h - padBottom);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();
    }

    // Draw Stroke Line
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      const xc = (points[i - 1].x + points[i].x) / 2;
      const yc = (points[i - 1].y + points[i].y) / 2;
      ctx.quadraticCurveTo(points[i - 1].x, points[i - 1].y, xc, yc);
    }
    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    ctx.strokeStyle = this.options.color;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Pulse dot at latest point
    const last = points[points.length - 1];
    ctx.beginPath();
    ctx.arc(last.x, last.y, 4, 0, Math.PI * 2);
    ctx.fillStyle = this.options.color;
    ctx.shadowColor = this.options.color;
    ctx.shadowBlur = 8;
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  hexToRgba(hex, alpha) {
    let c;
    if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
      c = hex.substring(1).split('');
      if (c.length === 3) c = [c[0], c[0], c[1], c[1], c[2], c[2]];
      c = '0x' + c.join('');
      return `rgba(${(c >> 16) & 255}, ${(c >> 8) & 255}, ${c & 255}, ${alpha})`;
    }
    return hex;
  }
}

window.MiniChart = MiniChart;
