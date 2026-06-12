import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import animation
from matplotlib.patches import FancyArrowPatch

from .problem import Color, Move

# Colore di riempimento delle celle per ogni simbolo
CELL_FILL = {
    "B": "#7eb6e8",  # blu
    "Y": "#f5e17a",  # giallo
    "G": "#8fd49a",  # verde
    "T": "#e0e0e0",  # cella di partenza (non colorata)
}


def _draw_grid(ax, grid, start_pos=None, head_pos=None, cell_fontsize=14, head_fontsize=15):
    """Disegna la griglia colorata su un axes (riga 0 in alto)."""
    rows, cols = len(grid), len(grid[0])
    for r in range(rows):
        for c in range(cols):
            symbol = getattr(grid[r][c], "symbol", grid[r][c])
            ax.add_patch(
                mpatches.Rectangle(
                    (c, rows - 1 - r), 1, 1,
                    facecolor=CELL_FILL.get(symbol, "white"),
                    edgecolor="black", linewidth=1.5,
                )
            )
            # La cella EMPTY ha simbolo "T" ma è solo la casella di partenza:
            # la T vera è la testina, disegnata a parte sulla posizione corrente
            if symbol != "T":
                ax.text(
                    c + 0.5, rows - 1 - r + 0.5, symbol,
                    ha="center", va="center", fontsize=cell_fontsize,
                    fontweight="bold", color="#333333",
                )
    # Evidenzia la cella di partenza (dove la testina deve tornare)
    if start_pos is not None:
        r, c = start_pos
        ax.add_patch(
            mpatches.Rectangle(
                (c, rows - 1 - r), 1, 1,
                facecolor="none", edgecolor="red", linewidth=3,
            )
        )
    # Posizione corrente della testina: "T" rossa che si sposta con i movimenti
    if head_pos is not None:
        r, c = head_pos
        ax.text(c + 0.5, rows - 1 - r + 0.5, "T",
                ha="center", va="center", fontsize=head_fontsize, fontweight="bold",
                color="red", zorder=7,
                bbox=dict(boxstyle="circle,pad=0.25", fc="white", ec="red", lw=1.5))
    ax.set_xlim(-0.1, cols + 0.1)
    ax.set_ylim(-0.1, rows + 0.1)
    ax.set_aspect("equal")
    ax.axis("off")


def _cell_center(pos, rows):
    """Centro della cella (r, c) in coordinate del plot."""
    r, c = pos
    return (c + 0.5, rows - 1 - r + 0.5)


def _draw_path(ax, problem, solution, title=""):
    """
    Disegna su un axes il riassunto dell'intera soluzione:
      - griglia iniziale colorata, partenza bordata di rosso
      - frecce numerate per ogni movimento della testina
      - cerchio verde numerato dove la cella viene colorata
    Le frecce su tratte ripetute vengono distribuite simmetricamente
    rispetto al centro della cella per non sovrapporsi.
    """
    grid = problem.initial.grid
    rows = len(grid)
    actions = solution.solution()

    _draw_grid(ax, grid, start_pos=problem.start_pos, head_pos=problem.start_pos)

    # Prima passata: conta quante volte ogni tratta viene percorsa, così gli
    # offset si possono distribuire simmetricamente attorno al centro cella
    # (1 freccia -> centrata; 2 -> ±0.11; 3 -> -0.22, 0, +0.22; ...)
    pos = problem.start_pos
    edge_total = {}
    for action in actions:
        if isinstance(action, Move):
            dr, dc = action.value
            new_pos = (pos[0] + dr, pos[1] + dc)
            key = frozenset((pos, new_pos))
            edge_total[key] = edge_total.get(key, 0) + 1
            pos = new_pos

    pos = problem.start_pos
    edge_count = {}  # quante volte una tratta è già stata percorsa

    for i, action in enumerate(actions, 1):
        if isinstance(action, Move):
            dr, dc = action.value
            new_pos = (pos[0] + dr, pos[1] + dc)

            key = frozenset((pos, new_pos))
            n = edge_count.get(key, 0)
            edge_count[key] = n + 1
            offset = (n - (edge_total[key] - 1) / 2) * 0.22
            # perpendicolare al movimento: se mi muovo in orizzontale sfalso in verticale e viceversa
            ox, oy = (0.0, offset) if dc != 0 else (offset, 0.0)

            x1, y1 = _cell_center(pos, rows)
            x2, y2 = _cell_center(new_pos, rows)
            arrow = FancyArrowPatch(
                (x1 + ox, y1 + oy), (x2 + ox, y2 + oy),
                arrowstyle="-|>", mutation_scale=11,
                color="#d62728", linewidth=1.2, shrinkA=8, shrinkB=8, zorder=5,
            )
            ax.add_patch(arrow)
            # Numero dello step verso la coda della freccia, lontano dalla punta
            xm = x1 + 0.3 * (x2 - x1)
            ym = y1 + 0.3 * (y2 - y1)
            ax.text(xm + ox, ym + oy, str(i),
                    fontsize=7, fontweight="bold", color="white", zorder=6,
                    ha="center", va="center",
                    bbox=dict(boxstyle="circle,pad=0.12", fc="#d62728", ec="none"))
            pos = new_pos
        elif isinstance(action, Color):
            # Cerchio numerato nell'angolo della cella: qui la testina ha colorato
            x, y = _cell_center(pos, rows)
            ax.text(x + 0.3, y - 0.3, str(i),
                    fontsize=9, fontweight="bold", color="white", zorder=6,
                    ha="center", va="center",
                    bbox=dict(boxstyle="circle,pad=0.2", fc="#2ca02c", ec="black"))

    ax.set_title(
        f"{title}\n{len(actions)} steps, cost {solution.path_cost}\n"
        "red arrows = moves, green circles = colorings",
        fontsize=9,
    )


def _draw_steps(axes, problem, solution):
    """
    Disegna una mini-griglia per ogni step della soluzione (stato DOPO l'azione)
    sugli axes forniti, mostrando come la griglia evolve fino allo stato finale.
    """
    actions = solution.solution()
    # Ricostruisce la sequenza di stati replicando le azioni dal nodo iniziale
    states = [problem.initial]
    for action in actions:
        states.append(problem.result(states[-1], action))

    for idx, (ax, state) in enumerate(zip(axes, states)):
        _draw_grid(ax, state.grid, start_pos=problem.start_pos,
                   head_pos=state.pos, cell_fontsize=8, head_fontsize=8)
        if idx == 0:
            ax.set_title("Initial", fontsize=8)
        else:
            ax.set_title(f"{idx}. {actions[idx - 1]}", fontsize=7)

    # Nasconde gli assi avanzati
    for ax in axes[len(states):]:
        ax.axis("off")

    return len(states)


def animate_solution(problem, solution, title="", interval=700):
    """
    Anima la soluzione step-by-step: un frame per ogni azione, con la
    testina che si muove e le celle che cambiano colore.
    Restituisce una FuncAnimation: nel notebook mostrarla con
    HTML(anim.to_jshtml()) per avere i controlli play/pausa/step.
    """
    if solution is None:
        print(f"✗ No solution to animate for {title}")
        return None

    actions = solution.solution()
    # Ricostruisce la sequenza di stati replicando le azioni dal nodo iniziale
    states = [problem.initial]
    for action in actions:
        states.append(problem.result(states[-1], action))

    grid = problem.initial.grid
    fig, ax = plt.subplots(
        figsize=(max(3.5, len(grid[0]) * 1.2), max(3.5, len(grid) * 1.2))
    )

    def frame(i):
        ax.clear()
        _draw_grid(ax, states[i].grid, start_pos=problem.start_pos,
                   head_pos=states[i].pos)
        label = "Initial" if i == 0 else f"step {i}/{len(actions)}: {actions[i - 1]}"
        ax.set_title(f"{title}\n{label}", fontsize=10)

    anim = animation.FuncAnimation(
        fig, frame, frames=len(states), interval=interval, repeat=True
    )
    plt.close(fig)  # evita la figura statica duplicata sotto l'animazione
    return anim


def plot_initial_state(problem):
    """
    Mostra lo stato iniziale del problema come griglia colorata:
    testina sulla posizione di partenza (bordo rosso) e, nel titolo,
    posizione e colore target scelto per la colorazione uniforme.
    """
    grid = problem.initial.grid
    fig, ax = plt.subplots(
        figsize=(max(3.5, len(grid[0]) * 1.2), max(3.5, len(grid) * 1.2))
    )
    _draw_grid(ax, grid, start_pos=problem.start_pos)
    # "T" semplice nella cella di partenza (niente cerchio: la testina non si è ancora mossa)
    x, y = _cell_center(problem.start_pos, len(grid))
    ax.text(x, y, "T", ha="center", va="center", fontsize=14,
            fontweight="bold", color="#333333")
    ax.set_title(
        f"Initial state\nhead at {problem.initial.pos}, "
        f"target color: {problem.target_color.symbol}",
        fontsize=10,
    )
    plt.tight_layout()
    plt.show()


def plot_solution(problem, solution, title="", step_cols=7):
    """
    Visualizzazione completa della soluzione in UNA figura:
    a sinistra il riassunto del percorso (frecce), a destra
    l'evoluzione passo-passo della griglia.
    """
    if solution is None:
        print(f"✗ No solution to draw for {title}")
        return

    n_states = len(solution.solution()) + 1
    step_rows = (n_states + step_cols - 1) // step_cols
    grid_rows = len(problem.initial.grid)
    grid_cols = len(problem.initial.grid[0])

    # Pannello sinistro compatto: la dimensione della figura è dettata dagli
    # step a destra, il path si adatta mantenendo le proporzioni
    path_w = max(3.0, grid_cols * 1.0)
    steps_w = step_cols * 1.5
    height = max(grid_rows * 1.0 + 1.2, step_rows * 1.7)

    fig = plt.figure(figsize=(path_w + steps_w, height))
    gs = fig.add_gridspec(1, 2, width_ratios=[path_w, steps_w], wspace=0.05)

    # Sinistra: percorso riassuntivo
    ax_path = fig.add_subplot(gs[0, 0])
    _draw_path(ax_path, problem, solution, title)

    # Destra: evoluzione passo-passo
    sub = gs[0, 1].subgridspec(step_rows, step_cols, hspace=0.45, wspace=0.1)
    axes = [fig.add_subplot(sub[i]) for i in range(step_rows * step_cols)]
    _draw_steps(axes, problem, solution)

    plt.show()


def plot_solution_path(problem, solution, title=""):
    """Solo il riassunto del percorso (frecce) in una figura dedicata."""
    if solution is None:
        print(f"✗ No solution to draw for {title}")
        return

    grid = problem.initial.grid
    fig, ax = plt.subplots(
        figsize=(max(4, len(grid[0]) * 1.6), max(4, len(grid) * 1.6))
    )
    _draw_path(ax, problem, solution, title)
    plt.tight_layout()
    plt.show()


def plot_solution_steps(problem, solution, title="", max_cols=7):
    """Solo l'evoluzione passo-passo, una mini-griglia per azione."""
    if solution is None:
        print(f"✗ No solution to draw for {title}")
        return

    n = len(solution.solution()) + 1
    ncols = min(max_cols, n)
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 1.9, nrows * 2.1))
    axes = [axes] if n == 1 else list(axes.flat)
    _draw_steps(axes, problem, solution)

    fig.suptitle(f"{title} — step-by-step evolution", fontsize=12)
    plt.tight_layout()
    plt.show()
