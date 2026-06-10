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
    show_images([vis], ["Linee griglia rilevate (verde=H, blu=V)"])


def draw_intersections(img, pts):
    """Visualizza i punti di intersezione tra le linee della griglia"""
    vis = img.copy()
    # Punti di intersezione in rosso
    for i in range(pts.shape[0]):
        for j in range(pts.shape[1]):
            x, y = int(pts[i, j, 0]), int(pts[i, j, 1])
            cv.circle(vis, (x, y), 5, (0, 0, 255), -1)
    show_images([vis], ["Intersezioni griglia"])


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
    show_images([vis], ["Segmenti Hough (grigio=scartati, verde=H, blu=V)"])


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
    plt.suptitle("Celle estratte", fontweight="bold")
    plt.tight_layout()
    plt.show()


def print_matrix(matrix):
    print("\nMATRICE RICONOSCIUTA:")
    cols = len(matrix[0]) if matrix else 0
    print("   " + "  ".join(str(j) for j in range(cols)))
    print("   " + "──" * cols)
    for i, row in enumerate(matrix):
        print(f"{i:2} │ " + "  ".join(str(c) for c in row))
    print()
