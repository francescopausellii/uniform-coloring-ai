import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt


def show_images(imgs, titles=None, cmap="gray"):
    """
    Utility per visualizzare più immagini affiancate con titoli opzionali
    """
    n = len(imgs)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4))
    if n == 1:
        axes = [axes]
    for i, (ax, img) in enumerate(zip(axes, imgs)):
        disp = cv.cvtColor(img, cv.COLOR_BGR2RGB) if len(img.shape) == 3 else img
        ax.imshow(disp, cmap=cmap if len(img.shape) == 2 else None)
        ax.axis("off")
        if titles:
            ax.set_title(titles[i], fontsize=10)
    plt.tight_layout()
    plt.show()


def draw_grid_lines(img, h_lines, v_lines):
    """Visualizza le linee della griglia sull'immagine originale"""
    vis = img.copy()
    # Linee orizzontali in verde, verticali in blu
    for l in h_lines:
        cv.line(vis, l["p1"], l["p2"], (0, 220, 80), 2)
    for l in v_lines:
        cv.line(vis, l["p1"], l["p2"], (0, 100, 255), 2)
    show_images([vis], [f"Grid lines ({len(h_lines)} H green, {len(v_lines)} V blue)"])


def draw_intersections(img, pts):
    """Visualizza i punti di intersezione tra le linee della griglia"""
    vis = img.copy()
    # Punti di intersezione in rosso
    for i in range(pts.shape[0]):
        for j in range(pts.shape[1]):
            x, y = int(pts[i, j, 0]), int(pts[i, j, 1])
            cv.circle(vis, (x, y), 5, (0, 0, 255), -1)
    show_images([vis], ["Grid intersections"])


def draw_all_segments(img, segs, horiz, vert):
    """Visualizza tutti i segmenti rilevati, evidenziando quelli orizzontali e verticali"""
    vis = img.copy()
    # Segmenti in grigio chiaro, orizzontali in verde, verticali in blu
    for s in segs:
        cv.line(vis, s[:2], s[2:], (150, 150, 150), 1)
    for s in horiz:
        cv.line(vis, s[:2], s[2:], (0, 200, 80), 2)
    for s in vert:
        cv.line(vis, s[:2], s[2:], (0, 100, 255), 2)
    show_images([vis], [f"Hough segments: {len(segs)} (grey=discarded, green=H, blue=V)"])


def show_preprocessing(img, gray, edges, grid_mask):
    """
    Riassume il preprocessing in UNA figura: originale, scala di grigi,
    bordi Canny e maschera della griglia (solo linee, lettere rimosse).
    """
    h, w = gray.shape
    show_images(
        [img, gray, edges, grid_mask],
        [f"Original ({w}x{h} px)", "Grayscale", "Canny edges", "Grid mask"],
    )


def show_line_detection(img, segs, horiz, vert, h_lines, v_lines, pts):
    """
    Riassume il rilevamento linee in UNA figura con i conteggi nei titoli:
      1. segmenti Hough classificati (H/V/scartati)
      2. linee di griglia fittate dai cluster
      3. intersezioni -> dimensione della griglia di celle
    """
    # Pannello 1: segmenti classificati
    vis_segs = img.copy()
    for s in segs:
        cv.line(vis_segs, s[:2], s[2:], (150, 150, 150), 1)
    for s in horiz:
        cv.line(vis_segs, s[:2], s[2:], (0, 200, 80), 2)
    for s in vert:
        cv.line(vis_segs, s[:2], s[2:], (0, 100, 255), 2)

    # Pannello 2: linee di griglia fittate
    vis_lines = img.copy()
    for l in h_lines:
        cv.line(vis_lines, l["p1"], l["p2"], (0, 220, 80), 2)
    for l in v_lines:
        cv.line(vis_lines, l["p1"], l["p2"], (0, 100, 255), 2)

    # Pannello 3: intersezioni
    vis_pts = img.copy()
    for i in range(pts.shape[0]):
        for j in range(pts.shape[1]):
            x, y = int(pts[i, j, 0]), int(pts[i, j, 1])
            cv.circle(vis_pts, (x, y), 5, (0, 0, 255), -1)

    n_rows, n_cols = pts.shape[0] - 1, pts.shape[1] - 1
    show_images(
        [vis_segs, vis_lines, vis_pts],
        [
            f"Hough segments: {len(segs)} ({len(horiz)} H green, {len(vert)} V blue,\n"
            f"{len(segs) - len(horiz) - len(vert)} discarded grey)",
            f"Fitted grid lines ({len(h_lines)} H, {len(v_lines)} V)",
            f"Intersections: {pts.shape[0]}x{pts.shape[1]} -> {n_rows}x{n_cols} cells",
        ],
    )


def visualize_cells(cells_2d):
    """Visualizza tutte le celle estratte in una griglia"""
    n_r = len(cells_2d)
    n_c = len(cells_2d[0]) if cells_2d else 0
    fig, axes = plt.subplots(n_r, n_c, figsize=(n_c * 1.3, n_r * 1.3))
    if n_r == 1 and n_c == 1:
        axes = np.array([[axes]])
    elif n_r == 1:
        axes = axes[np.newaxis, :]
    elif n_c == 1:
        axes = axes[:, np.newaxis]
    for r in range(n_r):
        for c in range(n_c):
            axes[r, c].imshow(cells_2d[r][c], cmap="gray")
            axes[r, c].axis("off")
            axes[r, c].set_title(f"{r},{c}", fontsize=6)
    plt.suptitle("Extracted cells", fontweight="bold")
    plt.tight_layout()
    plt.show()


# Colore di riempimento delle celle per ogni lettera riconosciuta
CELL_FILL = {
    "B": "#7eb6e8",  # blu
    "Y": "#f5e17a",  # giallo
    "G": "#8fd49a",  # verde
    "T": "#e0e0e0",  # testina / cella di partenza
}


def show_recognized_cells(cells_2d, matrix):
    """
    Mosaico delle celle estratte con la lettera predetta dalla rete come
    titolo, su sfondo del colore corrispondente: a colpo d'occhio si vede
    cosa ha riconosciuto il modello per ogni cella.
    """
    n_r = len(cells_2d)
    n_c = len(cells_2d[0]) if cells_2d else 0
    fig, axes = plt.subplots(n_r, n_c, figsize=(n_c * 1.5, n_r * 1.6))
    axes = np.array(axes).reshape(n_r, n_c)
    for r in range(n_r):
        for c in range(n_c):
            axes[r, c].imshow(cells_2d[r][c], cmap="gray")
            axes[r, c].axis("off")
            pred = matrix[r][c]
            axes[r, c].set_title(
                f" {pred} ", fontsize=10, fontweight="bold",
                backgroundcolor=CELL_FILL.get(pred, "white"),
            )
    plt.suptitle("Extracted cells and predicted letter", fontweight="bold")
    plt.tight_layout()
    plt.show()


def _draw_grid_matrix(ax, matrix, title):
    """Disegna la matrice di lettere come griglia colorata su un axes."""
    rows, cols = len(matrix), len(matrix[0])
    for r in range(rows):
        for c in range(cols):
            symbol = matrix[r][c]
            ax.add_patch(
                plt.Rectangle(
                    (c, rows - 1 - r), 1, 1,
                    facecolor=CELL_FILL.get(symbol, "white"),
                    edgecolor="black", linewidth=1.5,
                )
            )
            ax.text(c + 0.5, rows - 1 - r + 0.5, symbol,
                    ha="center", va="center", fontsize=14,
                    fontweight="bold", color="#333333")
    ax.set_xlim(-0.1, cols + 0.1)
    ax.set_ylim(-0.1, rows + 0.1)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=11)


def show_grid_matrix(matrix, title="Recognized grid"):
    """Griglia colorata in una figura dedicata (es. griglia fornita a mano)."""
    rows, cols = len(matrix), len(matrix[0])
    fig, ax = plt.subplots(figsize=(max(3, cols * 1.1), max(3, rows * 1.1)))
    _draw_grid_matrix(ax, matrix, title)
    plt.tight_layout()
    plt.show()


def show_recognition_result(cells_2d, matrix):
    """
    Risultato del riconoscimento in UNA figura: a sinistra il mosaico delle
    celle estratte con la lettera predetta, a destra la griglia ricostruita.
    """
    n_r = len(cells_2d)
    n_c = len(cells_2d[0]) if cells_2d else 0

    cells_w = n_c * 1.5
    grid_w = max(3, n_c * 1.1)
    fig = plt.figure(figsize=(cells_w + grid_w, max(3, n_r * 1.7)))
    gs = fig.add_gridspec(1, 2, width_ratios=[cells_w, grid_w], wspace=0.15)

    # Sinistra: mosaico celle + predizioni
    sub = gs[0, 0].subgridspec(n_r, n_c, hspace=0.35, wspace=0.05)
    for r in range(n_r):
        for c in range(n_c):
            ax = fig.add_subplot(sub[r, c])
            ax.imshow(cells_2d[r][c], cmap="gray")
            ax.axis("off")
            pred = matrix[r][c]
            ax.set_title(
                f" {pred} ", fontsize=10, fontweight="bold",
                backgroundcolor=CELL_FILL.get(pred, "white"),
            )

    # Destra: griglia ricostruita a colori
    ax_grid = fig.add_subplot(gs[0, 1])
    _draw_grid_matrix(ax_grid, matrix, "Recognized grid")

    fig.suptitle("Extracted cells and predicted letters", fontweight="bold")
    plt.show()


def print_matrix(matrix):
    print("\nMATRICE RICONOSCIUTA:")
    cols = len(matrix[0]) if matrix else 0
    print("   " + "  ".join(str(j) for j in range(cols)))
    print("   " + "──" * cols)
    for i, row in enumerate(matrix):
        print(f"{i:2} │ " + "  ".join(str(c) for c in row))
    print()
