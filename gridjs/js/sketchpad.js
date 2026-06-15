// GridSketchPad: canvas con griglia rows x cols su cui scrivere a mano.
// Sfondo bianco + linee scure + tratti scuri => formato atteso dalla
// pipeline OpenCV (detect_grid_morph).
class GridSketchPad {
  constructor(container, opts = {}) {
    this.rows = opts.rows ?? 4;
    this.cols = opts.cols ?? 4;
    this.cell = opts.cell ?? 80;
    this.margin = opts.margin ?? 20;
    this.penWidth = opts.penWidth ?? 2;
    this.showGuide = opts.showGuide ?? true;

    this.width = this.margin * 2 + this.cols * this.cell;
    this.height = this.margin * 2 + this.rows * this.cell;

    this.canvas = document.createElement("canvas");
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    this.canvas.style = "background-color:white; box-shadow:0 0 8px 1px #888; touch-action:none;";
    container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext("2d");

    this.paths = [];
    this.isDrawing = false;

    this.#addEventListeners();
    this.render();
  }

  reset() {
    this.paths = [];
    this.isDrawing = false;
    this.render();
  }

  undo() {
    this.paths.pop();
    this.render();
  }

  render() {
    this.ctx.fillStyle = "white";
    this.ctx.fillRect(0, 0, this.width, this.height);
    // guida tenue solo a schermo: NON viene esportata
    if (this.showGuide) {
      draw.grid(this.ctx, this.rows, this.cols, this.cell, this.margin, "#d8d8d8", 1);
    }
    draw.pens(this.ctx, this.paths, "black", this.penWidth);
  }

  toggleGuide() {
    this.showGuide = !this.showGuide;
    this.render();
  }

  // PNG con solo i tratti disegnati a mano su bianco (griglia inclusa = quella
  // che disegni tu). La guida grigia viene esclusa dall'export.
  toDataURL() {
    const guide = this.showGuide;
    this.showGuide = false;
    this.render();
    const url = this.canvas.toDataURL("image/png");
    this.showGuide = guide;
    this.render();
    return url;
  }

  // PNG con griglia automatica (linee nere piene generate dal programma) +
  // i tratti disegnati a mano. La guida grigia viene esclusa.
  toDataURLWithGrid() {
    const guide = this.showGuide;
    this.showGuide = false;
    this.ctx.fillStyle = "white";
    this.ctx.fillRect(0, 0, this.width, this.height);
    draw.grid(this.ctx, this.rows, this.cols, this.cell, this.margin, "black", 2);
    draw.pens(this.ctx, this.paths, "black", this.penWidth);
    const url = this.canvas.toDataURL("image/png");
    this.showGuide = guide;
    this.render();
    return url;
  }

  #getPos(evt) {
    const rect = this.canvas.getBoundingClientRect();
    const src = evt.touches ? evt.touches[0] : evt;
    return [
      Math.round(src.clientX - rect.left),
      Math.round(src.clientY - rect.top),
      performance.now(),
    ];
  }

  #start = (evt) => {
    evt.preventDefault();
    this.paths.push([this.#getPos(evt)]);
    this.isDrawing = true;
  };

  #move = (evt) => {
    if (!this.isDrawing) return;
    evt.preventDefault();
    this.paths[this.paths.length - 1].push(this.#getPos(evt));
    this.render();
  };

  #end = () => {
    this.isDrawing = false;
  };

  #addEventListeners() {
    this.canvas.addEventListener("mousedown", this.#start);
    this.canvas.addEventListener("mousemove", this.#move);
    document.addEventListener("mouseup", this.#end);

    this.canvas.addEventListener("touchstart", this.#start, { passive: false });
    this.canvas.addEventListener("touchmove", this.#move, { passive: false });
    document.addEventListener("touchend", this.#end);

    document.addEventListener("keydown", (evt) => {
      if (evt.ctrlKey && evt.key === "z") {
        evt.preventDefault();
        this.undo();
      }
    });
  }
}
