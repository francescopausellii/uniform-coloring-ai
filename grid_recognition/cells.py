import cv2 as cv
import numpy as np


def extract_cell_from_intersections(gray, pts, row, col, padding=16, target=(128, 128)):
    """
    Estrae la cella (row, col) usando i 4 angoli calcolati dalle intersezioni.
    Applica una prospettiva corretta (warpPerspective) per raddrizzare celle storte.

    La cella viene estratta ad ALTA risoluzione (128x128): la riduzione a 28x28
    avviene solo in prepare_cell_for_emnist, DOPO la binarizzazione. Warpando
    direttamente a 28x28 i tratti delle lettere si riducono a 1-2 px sfumati e
    la soglia adattiva + pulizia morfologica li distruggono (es. la B perdeva
    la spina verticale e veniva classificata come Y).
    """
    # Prende i 4 angoli della cella dalla matrice di intersezioni
    tl = pts[row, col]  # top-left
    tr = pts[row, col + 1]  # top-right
    bl = pts[row + 1, col]  # bottom-left
    br = pts[row + 1, col + 1]  # bottom-right

    # Forma reale della cella nella prospettiva originale
    src = np.array([tl, tr, br, bl], dtype=np.float32)

    # Forma rettangolare per la cella estratta
    dst = np.array(
        [
            [0, 0],
            [target[0] - 1, 0],
            [target[0] - 1, target[1] - 1],
            [0, target[1] - 1],
        ],
        dtype=np.float32,
    )

    # Matrice di trasformazione prospettica per mappare punti src in dst
    M = cv.getPerspectiveTransform(src, dst)
    cell = cv.warpPerspective(gray, M, target)

    # Padding interno: rimuove i residui delle linee di griglia sul bordo
    if padding > 0:
        cell = cell[padding:-padding, padding:-padding]
        cell = cv.resize(cell, target, interpolation=cv.INTER_AREA)

    return cell


def extract_all_cells(gray, pts):
    """
    Estrae tutte le celle dalla matrice di intersezioni.
    pts ha shape (n_h, n_v, 2) → griglia di (n_h-1) x (n_v-1) celle.
    Restituisce cells_2d: lista 2D di array numpy.
    """
    # Con n_h linee orizzontali e n_v linee verticali, ci sono (n_h-1) x (n_v-1) celle
    n_rows = pts.shape[0] - 1
    n_cols = pts.shape[1] - 1
    cells_2d = []

    for r in range(n_rows):
        row_cells = []
        for c in range(n_cols):
            # Singola cella estratta
            cell = extract_cell_from_intersections(gray, pts, r, c)
            row_cells.append(cell)
        cells_2d.append(row_cells)

    return cells_2d


def prepare_cell_for_emnist(cell_gray, target_size=(28, 28)):
    """
    Trasforma una cella grezza (grayscale uint8, alta risoluzione) nel formato EMNIST.

    Pipeline:
      1. Denoising adattivo
      2. Binarizzazione → lettera bianca su sfondo nero (come EMNIST)
      3. Pulizia morfologica + filtro componenti connesse
      4. Bounding box del carattere → crop + padding
      5. Resize a target_size con aspect ratio preservato
      6. Normalizzazione [0.0, 1.0]

    Input:  numpy array (H, W) uint8
    Output: numpy array (28, 28) float32, pronto per model.predict()
    """
    # Rimuove le imperfezioni della scrittura
    # h=12: più alto per immagini più rumorose, più basso per immagini pulite. Se è troppo alto sfuma i tratti sottili.
    denoised = cv.fastNlMeansDenoising(
        cell_gray, h=12, templateWindowSize=7, searchWindowSize=21
    )

    # Converte l'immagine in bianco e nero
    # blockSize adattivo: deve restare piu' grande dello spessore del tratto
    # (~8-10 px su celle 128x128), altrimenti l'interno del tratto viene
    # scambiato per sfondo e la lettera si svuota.
    bs = max(17, (min(cell_gray.shape) // 5) | 1)  # dispari, >= 17
    binary = cv.adaptiveThreshold(
        denoised,
        255,
        cv.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv.THRESH_BINARY_INV,  # INV → lettera bianca, sfondo nero (EMNIST)
        blockSize=bs,
        C=8,
    )

    # Elimina pixel isolati e chiude piccoli buchi nel tratto.
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv.morphologyEx(
        binary, cv.MORPH_OPEN, kernel, iterations=1
    )  # toglie rumore
    cleaned = cv.morphologyEx(
        cleaned, cv.MORPH_CLOSE, kernel, iterations=1
    )  # chiude buchi

    # Nelle griglie disegnate a mano le linee sono ondulate e il padding del
    # crop non basta a eliminarle: frammenti di linea entrano nella cella,
    # allargano il bounding box e schiacciano la lettera in un angolo.
    # Teniamo la componente piu' grande (la lettera) e le componenti che NON
    # toccano il bordo e hanno area >= 5% della maggiore (tratti staccati
    # della stessa lettera); i frammenti di griglia toccano sempre il bordo.
    n_cc, cc_labels, stats, _ = cv.connectedComponentsWithStats(cleaned, connectivity=8)
    if n_cc > 2:  # piu' di una componente oltre lo sfondo
        H_cc, W_cc = cleaned.shape
        areas = stats[1:, cv.CC_STAT_AREA]
        main = 1 + int(np.argmax(areas))
        keep = np.zeros_like(cleaned)
        for i in range(1, n_cc):
            x0, y0, w0, h0, a0 = stats[i]
            touches_border = x0 == 0 or y0 == 0 or x0 + w0 >= W_cc or y0 + h0 >= H_cc
            if i == main or (not touches_border and a0 >= 0.05 * areas.max()):
                keep[cc_labels == i] = 255
        cleaned = keep

    # Trova il rettangolo minimo che contiene tutti i pixel bianchi.
    # Se la cella è vuota (nessun pixel bianco) restituisce un array di zeri.
    coords = cv.findNonZero(cleaned)
    if coords is None:
        # Cella vuota (lettera assente o completamente rumore)
        return np.zeros(target_size, dtype=np.float32)

    x, y, w, h = cv.boundingRect(coords)

    # Margine di sicurezza: 15% della dimensione maggiore, minimo 2px
    margin = max(2, int(max(w, h) * 0.15))
    H_cell, W_cell = cleaned.shape
    x1 = max(0, x - margin)
    y1 = max(0, y - margin)
    x2 = min(W_cell, x + w + margin)
    y2 = min(H_cell, y + h + margin)

    cropped = cleaned[y1:y2, x1:x2]

    # EMNIST centra il carattere in una canvas 28×28 con bordo.
    # Facciamo lo stesso: resize a max 20×20, poi padding centrato a 28×28.
    inner = target_size[0] - 8  # 20px: lascia 4px di bordo per lato
    ch, cw = cropped.shape
    scale = inner / max(ch, cw)
    new_h = max(1, int(ch * scale))
    new_w = max(1, int(cw * scale))
    resized = cv.resize(cropped, (new_w, new_h), interpolation=cv.INTER_AREA)

    # Padding centrato
    canvas = np.zeros(target_size, dtype=np.uint8)
    pad_y = (target_size[1] - new_h) // 2
    pad_x = (target_size[0] - new_w) // 2
    canvas[pad_y : pad_y + new_h, pad_x : pad_x + new_w] = resized

    # Normalizza i pixel
    normalized = canvas.astype(np.float32) / 255.0

    return normalized
