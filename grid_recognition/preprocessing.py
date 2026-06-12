import cv2 as cv

from .visualization import show_images


def preparation(path, show=False):
    """
    Carica l'immagine, la converte in scala di grigi e ne estrae i contorni (Canny).
    """
    img = cv.imread(path)
    if img is None:
        raise FileNotFoundError(f"Immagine non trovata: {path}")

    # Non servono i canali di colore, solo grigi
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Sfocature per migliore rilevamento bordi
    blurred = cv.GaussianBlur(gray, (5, 5), 0)

    # Canny con soglie automatiche (metodo Otsu)
    otsu_thresh, _ = cv.threshold(blurred, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

    # Rilevamento bordi con Canny usando le soglie calcolate da Otsu
    edges = cv.Canny(blurred, threshold1=otsu_thresh * 0.5, threshold2=otsu_thresh)

    if show:
        show_images([img, gray, edges], ["Original", "Grayscale", "Canny edges"])

    return img, gray, edges


def extract_grid_mask(gray, show=False):
    """
    Isola SOLO le linee della griglia, eliminando i tratti delle lettere.
    Otsu globale (immagini sintetiche pulite, niente speckle da adaptive),
    poi erosione+dilatazione con kernel lungo 1D: sopravvive solo cio' che
    ha molti pixel continui in una direzione -> linee griglia, non lettere.
    """

    # Immagine convertita in bianco e nero
    _, bw = cv.threshold(gray, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)

    h, w = gray.shape

    # Creazione rettangolo lungo
    hk = cv.getStructuringElement(cv.MORPH_RECT, (w // 10, 1))
    # Erosione per rimuovere le lettere
    hor = cv.dilate(cv.erode(bw, hk), hk)

    # Creazione rettangolo alto
    vk = cv.getStructuringElement(cv.MORPH_RECT, (1, h // 10))
    ver = cv.dilate(cv.erode(bw, vk), vk)

    # Maschera finale come somma di linee orizzontali e verticali
    grid = cv.add(hor, ver)
    if show:
        show_images(
            [bw, hor, ver, grid],
            ["Otsu binary", "H lines", "V lines", "Grid mask"],
        )
    return grid
