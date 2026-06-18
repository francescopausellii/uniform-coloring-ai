const draw = {};

draw.path = (ctx, path, color = "black", width = 3) => {
  if (path.length === 0) return;
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.beginPath();
  ctx.moveTo(...path[0]);
  for (let i = 1; i < path.length; i++) {
    ctx.lineTo(...path[i]);
  }
  ctx.stroke();
};

draw.paths = (ctx, paths, color = "black", width = 3) => {
  for (let path of paths) {
    draw.path(ctx, path, color, width);
  }
};

// Tratto stile penna stilografica: spessore variabile con la velocità del
// movimento (lento => spesso, veloce => sottile). Ogni punto e' [x, y, t].
draw.pen = (ctx, path, color = "black", base = 2.5) => {
  if (path.length === 0) return;
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  if (path.length === 1) {
    ctx.beginPath();
    ctx.arc(path[0][0], path[0][1], base / 2, 0, Math.PI * 2);
    ctx.fill();
    return;
  }

  const widthAt = (a, b) => {
    const dist = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const dt = Math.max(1, (b[2] ?? 0) - (a[2] ?? 0));
    const speed = dist / dt; // px/ms
    // mappa velocita' -> spessore: lento ~ base*2.2, veloce ~ base*0.5
    const w = base * (2.2 - Math.min(1.7, speed * 0.9));
    return Math.max(base * 0.5, w);
  };

  let prevW = widthAt(path[0], path[1]);
  for (let i = 1; i < path.length; i++) {
    const w = widthAt(path[i - 1], path[i]);
    const smoothed = (prevW + w) / 2;
    prevW = w;
    ctx.lineWidth = smoothed;
    ctx.beginPath();
    ctx.moveTo(path[i - 1][0], path[i - 1][1]);
    ctx.lineTo(path[i][0], path[i][1]);
    ctx.stroke();
  }
};

draw.pens = (ctx, paths, color = "black", base = 2.5) => {
  for (let path of paths) {
    draw.pen(ctx, path, color, base);
  }
};

// Linee di griglia: rows x cols celle di lato `cell`, con bordo `margin`.
draw.grid = (ctx, rows, cols, cell, margin, color = "black", width = 2) => {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  for (let r = 0; r <= rows; r++) {
    const y = margin + r * cell;
    ctx.beginPath();
    ctx.moveTo(margin, y);
    ctx.lineTo(margin + cols * cell, y);
    ctx.stroke();
  }
  for (let c = 0; c <= cols; c++) {
    const x = margin + c * cell;
    ctx.beginPath();
    ctx.moveTo(x, margin);
    ctx.lineTo(x, margin + rows * cell);
    ctx.stroke();
  }
};

if (typeof module !== "undefined") {
  module.exports = draw;
}
