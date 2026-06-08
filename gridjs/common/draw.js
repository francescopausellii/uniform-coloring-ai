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
