import numpy as np

from .cells import prepare_cell_for_emnist

# lettere riconosciute dal modello, nell'ordine degli indici di output
SELECTED_LABELS = ["B", "G", "T", "Y"]


def predict_cell(cell_img, model, labels=SELECTED_LABELS):
    # Prepara la cella per il modello EMNIST
    ready = prepare_cell_for_emnist(cell_img)  # (28, 28) float32

    # adatta input alla forma attesa dal modello caricato
    shape = model.input_shape[1:]  # es (28,28,1) o (784,)
    inp = ready.reshape((1,) + tuple(shape))

    # predice la lettera usando il modello addestrato, restituisce quella con probabilità più alta
    probs = model.predict(inp, verbose=0)[0]
    return labels[np.argmax(probs)]


def predict_grid(cells_2d, model, labels=SELECTED_LABELS):
    """Classifica ogni cella estratta e restituisce la matrice di lettere."""
    return [
        [predict_cell(cell, model, labels) for cell in row_cells]
        for row_cells in cells_2d
    ]
