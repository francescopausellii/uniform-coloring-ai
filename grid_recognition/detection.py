import cv2 as cv
import numpy as np

# Risoluzione del parametro 'rho' (la distanza dall'origine alla linea) in pixel.
# Un valore pari a 1 indica la massima precisione possibile (1 pixel).
HOUGH_RHO = 1

# Risoluzione del parametro 'theta' (l'angolo della linea) in radianti.
# Dividendo Pi Greco per 180 otteniamo l'equivalente di 1 grado (1°).
HOUGH_THETA = np.pi / 180  # risoluzione angolare (1°)

# Numero minimo di intersezioni (voti) nello "spazio di Hough" affinché una linea
# venga considerata valida. Più è basso, più l'algoritmo sarà sensibile e troverà
# anche linee deboli.
HOUGH_THRESHOLD = 60

# Lunghezza minima che deve avere un segmento per essere rilevato.
HOUGH_MIN_LEN = 40

# Distanza massima consentita tra due segmenti posizionati sulla stessa linea per unirli
HOUGH_MAX_GAP = 10

# Tolleranza in gradi per classificazione direzione segmenti
ANGLE_TOL_DEG = 15

# Se due segmenti paralleli sono < di questa distanza, allora sono considerati sulla stessa linea
POSITION_TOL_PX = 20

# Soglia relativa all'estensione della griglia: un cluster con span inferiore a
# questa frazione dello span massimo è un tratto di lettera, non una linea
SPAN_FRAC = 0.6


def detect_segments(edges):

    # Cerca segmenti partendo dai bordi rilevati da Canny
    segments = cv.HoughLinesP(
        edges,
        rho=HOUGH_RHO,
        theta=HOUGH_THETA,
        threshold=HOUGH_THRESHOLD,
        minLineLength=HOUGH_MIN_LEN,
        maxLineGap=HOUGH_MAX_GAP,
    )
    if segments is None:
        raise ValueError("Nessun segmento trovato")

    # Converto in lista di tuple
    segments = [tuple(s[0]) for s in segments]
    print(f"Segmenti Hough trovati: {len(segments)}")
    return segments


# controllo angoli dei segmenti per classificazione orizzontale o verticale
def segment_angle_deg(x1, y1, x2, y2):
    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
    if angle < -90:
        angle += 180
    if angle >= 90:
        angle -= 180
    return angle


def classify_segments(segs, angle_tol=ANGLE_TOL_DEG):

    horiz, vert = [], []
    for seg in segs:
        a = segment_angle_deg(*seg)
        # Se l'angolo è vicino a 0° → orizzontale, se è vicino a ±90° → verticale
        if abs(a) <= angle_tol:
            horiz.append(seg)
        elif abs(abs(a) - 90) <= angle_tol:
            vert.append(seg)
        # segmenti obliqui (lettere diagonali) vengono ignorati

    print(f"Segmenti orizzontali: {len(horiz)}")
    print(f"Segmenti verticali:   {len(vert)}")
    return horiz, vert


def segment_representative_position(segs, axis):
    """
    Per ogni segmento calcola la posizione "trasversale" media, per vedere la posizione della linea nello spazio:
      - linee orizzontali → media di y1, y2  (axis='y')
      - linee verticali   → media di x1, x2  (axis='x')
    Restituisce lista di (posizione, segmento).
    """
    result = []
    for s in segs:
        x1, y1, x2, y2 = s
        pos = (y1 + y2) / 2 if axis == "y" else (x1 + x2) / 2
        result.append((pos, s))
    return result


def cluster_lines_by_position(pos_segs, tol=POSITION_TOL_PX):
    """
    Raggruppa segmenti con posizione trasversale simile (entro `tol` pixel).
    Ogni gruppo rappresenta UNA linea della griglia.
    Restituisce lista di cluster, ciascuno = lista di segmenti.
    """
    sorted_ps = sorted(pos_segs, key=lambda x: x[0])
    clusters = []
    current = [sorted_ps[0]]
    for ps in sorted_ps[1:]:
        # Se la posizione è vicina all'ultima del cluster corrente, aggiungi, altrimenti inizia nuovo cluster
        if ps[0] - current[-1][0] <= tol:
            current.append(ps)
        else:
            clusters.append(current)
            current = [ps]
    clusters.append(current)
    return clusters


def _cluster_span(cluster, coord):
    vals = [v for _, s in cluster for v in (s[coord], s[coord + 2])]
    return max(vals) - min(vals)


def filter_clusters_by_span(horiz_cl, vert_cl, span_frac=SPAN_FRAC):
    """
    Scarta cluster generati dai tratti delle lettere (es. gamba della R,
    spina della B): una vera linea di griglia attraversa quasi tutta la
    griglia, un tratto di lettera resta dentro UNA cella.

    Soglia relativa all'estensione della griglia (non dell'immagine): la
    griglia puo' occupare solo una parte del frame, quindi confrontiamo lo
    span di ogni cluster con lo span massimo tra i cluster dello stesso asse.
    """
    if vert_cl:
        max_v_span = max(_cluster_span(cl, 1) for cl in vert_cl)
        vert_cl = [
            cl for cl in vert_cl if _cluster_span(cl, 1) >= span_frac * max_v_span
        ]
    if horiz_cl:
        max_h_span = max(_cluster_span(cl, 0) for cl in horiz_cl)
        horiz_cl = [
            cl for cl in horiz_cl if _cluster_span(cl, 0) >= span_frac * max_h_span
        ]
    print(f"Linee valide dopo filtro span -> H:{len(horiz_cl)} V:{len(vert_cl)}")
    return horiz_cl, vert_cl


def fit_line_from_cluster(cluster, img_shape):
    """
    Dati tutti i punti dei segmenti di un cluster, fa una regressione lineare
    (np.polyfit) e restituisce due punti estremi (p1, p2) che attraversano
    l'intera immagine.
    Questo è il 'averaging' dei punti che elimina l'effetto delle linee storte.
    """

    # Prendo tutti i punti estremi dei segmenti del cluster
    pts = []
    for _, (x1, y1, x2, y2) in cluster:
        pts.append((x1, y1))
        pts.append((x2, y2))

    pts = np.array(pts, dtype=float)
    h, w = img_shape[:2]

    # Decide se fittare y=f(x) o x=f(y) in base alla direzione prevalente
    span_x = pts[:, 0].max() - pts[:, 0].min()
    span_y = pts[:, 1].max() - pts[:, 1].min()

    if span_x >= span_y:
        coeffs = np.polyfit(
            pts[:, 0], pts[:, 1], 1
        )  # Regressione lineare di grado 1 -> restituisce la pendenza (a) e l'intercetta (b)
        x_start, x_end = (
            0,
            w - 1,
        )  # Estende la linea da sinistra a destra per tutta l'immagine
        y_start = int(
            np.polyval(coeffs, x_start)
        )  # Calcola l'altezza Y all'inizio dello schermo
        y_end = int(
            np.polyval(coeffs, x_end)
        )  # Calcola l'altezza Y alla fine dello schermo
        return (x_start, y_start), (x_end, y_end), coeffs, "h"

    else:  # linea prevalentemente verticale
        coeffs = np.polyfit(pts[:, 1], pts[:, 0], 1)  # x = a*y + b
        y_start, y_end = (
            0,
            h - 1,
        )  # Estende la linea dall'alto in basso per tutta l'immagine
        x_start = int(np.polyval(coeffs, y_start))
        x_end = int(np.polyval(coeffs, y_end))
        return (x_start, y_start), (x_end, y_end), coeffs, "v"


def line_intersection(line_h, line_v):
    """
    Intersezione esatta tra una linea orizzontale e una verticale,
    entrambe espresse come (coeffs, tipo).
    line_h: coeffs per y = a*x + b
    line_v: coeffs per x = a*y + b
    Restituisce (x, y) float.
    """

    # Calcola le equazioni delle linee e risolve il sistema per trovare l'intersezione
    a_h, b_h = line_h  # y = a_h * x + b_h
    a_v, b_v = line_v  # x = a_v * y + b_v
    # Sostituendo: y = a_h*(a_v*y + b_v) + b_h
    # y*(1 - a_h*a_v) = a_h*b_v + b_h
    denom = 1 - a_h * a_v
    if abs(denom) < 1e-9:  # linee parallele (non dovrebbe succedere)
        return None

    # Coordinate del punto di intersezione
    y = (a_h * b_v + b_h) / denom
    x = a_v * y + b_v
    return (x, y)


def build_grid_lines(horiz_clusters, vert_clusters, img_shape):
    """
    Per ogni cluster calcola la linea media.
    Ordina le linee orizzontali per y crescente, verticali per x crescente.
    Restituisce h_lines, v_lines (liste di dizionari con p1, p2, coeffs, tipo)
    """
    h_lines, v_lines = [], []

    # Trasforma i segmenti orizzontali in rette continue e calcola la posizione media per ordinare
    for cl in horiz_clusters:
        p1, p2, coeffs, tipo = fit_line_from_cluster(cl, img_shape)
        mid_y = (p1[1] + p2[1]) / 2
        h_lines.append(
            {"p1": p1, "p2": p2, "coeffs": coeffs, "tipo": tipo, "pos": mid_y}
        )

    # Trasforma i segmenti verticali in rette continue e calcola la posizione media per ordinare
    for cl in vert_clusters:
        p1, p2, coeffs, tipo = fit_line_from_cluster(cl, img_shape)
        mid_x = (p1[0] + p2[0]) / 2
        v_lines.append(
            {"p1": p1, "p2": p2, "coeffs": coeffs, "tipo": tipo, "pos": mid_x}
        )

    # Ordinamento linee orizzontali per posizione y e verticali per posizione x
    h_lines.sort(key=lambda l: l["pos"])
    v_lines.sort(key=lambda l: l["pos"])

    print(f"Linee griglia orizzontali: {len(h_lines)}")
    print(f"Linee griglia verticali:   {len(v_lines)}")
    return h_lines, v_lines


def compute_intersections(h_lines, v_lines):
    """
    Calcola tutte le intersezioni tra linee H e V.
    Restituisce matrice numpy (n_h, n_v, 2) di coordinate (x, y).
    """
    n_h, n_v = len(h_lines), len(v_lines)

    # Matrice di punti di intersezione
    pts = np.zeros((n_h, n_v, 2), dtype=float)

    # Calcola le intersezioni tra tutte le linee orizzontali e verticali
    for i, hl in enumerate(h_lines):
        for j, vl in enumerate(v_lines):
            pt = line_intersection(hl["coeffs"], vl["coeffs"])
            if pt is None:
                pt = (0, 0)
            pts[i, j] = pt
    return pts
