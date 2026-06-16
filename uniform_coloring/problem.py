from enum import Enum
from aima.search import Problem


class Color(Enum):
    """Colori disponibili. Ogni colore ha un simbolo e un costo di colorazione."""

    BLUE = ("B", 1)
    YELLOW = ("Y", 2)
    GREEN = ("G", 3)
    EMPTY = ("T", 0)  # Placeholder for the initial position of the head (T)

    def __init__(self, symbol, cost):
        self.symbol = symbol
        self.cost = cost

    def __lt__(self, other):
        if isinstance(other, Color):
            return self.cost < other.cost
        return NotImplemented


class Move(Enum):
    """Movimenti della testina come delta (riga, colonna), costo 1 ciascuno."""

    NORTH = (-1, 0)
    SOUTH = (1, 0)
    EAST = (0, 1)
    WEST = (0, -1)


class State:
    """
    Stato del problema: griglia + posizione testina.

    grid è una tupla di tuple (immutabile) per supportare hashing.
    L'ID "r,c:simboli" è usato per uguaglianza e hashing.
    """

    def __init__(self, grid, pos):
        self.grid = grid
        self.pos = pos
        symbols = ",".join(cell.symbol for row in grid for cell in row)
        self.id = f"{pos[0]},{pos[1]}:{symbols}"

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __lt__(self, other):
        return self.id < other.id


class UniformColoring(Problem):
    def __init__(self, grid_matrix, target_color=None):
        self.rows = len(grid_matrix)
        self.cols = len(grid_matrix[0])
        self.start_pos = None

        symbol_to_color = {c.symbol: c for c in Color if c != Color.EMPTY}

        initial_grid = []
        for r, row in enumerate(grid_matrix):
            row_colors = []
            for c, char in enumerate(row):
                if char == "T":
                    self.start_pos = (r, c)
                    row_colors.append(Color.EMPTY)
                else:
                    row_colors.append(symbol_to_color[char])
            initial_grid.append(tuple(row_colors))

        if target_color is not None:
            self.target_color = target_color
        else:
            non_start = [
                (r, c)
                for r in range(self.rows)
                for c in range(self.cols)
                if (r, c) != self.start_pos
            ]
            self.target_color = min(
                [Color.BLUE, Color.YELLOW, Color.GREEN],
                key=lambda tc: sum(
                    tc.cost for r, c in non_start if initial_grid[r][c] != tc
                ),
            )

        initial_state = State(tuple(initial_grid), self.start_pos)

        super().__init__(initial_state)

    def actions(self, state):
        """
        Movimenti (N/S/E/W) sempre ammessi se dentro la griglia.
        Colorazione con target_color solo se la cella non è già corretta e non è start_pos.
        """
        grid, pos = state.grid, state.pos
        r, c = pos
        possible_actions = []

        for move in Move:
            dr, dc = move.value
            new_r, new_c = r + dr, c + dc
            if 0 <= new_r < self.rows and 0 <= new_c < self.cols:
                possible_actions.append(move)

        if (r, c) != self.start_pos and grid[r][c] != self.target_color:
            possible_actions.append(self.target_color)

        return possible_actions

    def result(self, state, action):
        """Sposta la testina (Move) o colora la cella corrente (Color), restituendo un nuovo stato."""
        grid, pos = state.grid, state.pos

        if isinstance(action, Move):
            dr, dc = action.value
            return State(grid, (pos[0] + dr, pos[1] + dc))

        new_grid = [list(row) for row in grid]
        new_grid[pos[0]][pos[1]] = action
        return State(tuple(tuple(row) for row in new_grid), pos)

    def path_cost(self, c, state1, action, state2):
        """Costo: +1 per ogni movimento, +action.cost per una colorazione."""
        if isinstance(action, Move):
            return c + 1
        if isinstance(action, Color):
            return c + action.cost
        return c  # pragma: no cover

    def goal_test(self, state):
        """Goal: testina tornata a start_pos e tutte le celle (esclusa start) dello stesso colore."""
        if state.pos != self.start_pos:
            return False

        colors = {
            state.grid[r][c]
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) != self.start_pos
        }
        return not colors or len(colors) == 1

    def h(self, node):
        """
        Euristica di default: costo colorazione + lower bound sul movimento
        (distanza alla cella sbagliata più vicina + distanza di quella a start).
        Ammissibile ma poco informativa.
        """
        grid, pos = node.state.grid, node.state.pos

        # Somma dei costi per tutte le celle che non sono del target_color e non sono start_pos
        to_color = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if (r, c) != self.start_pos and grid[r][c] != self.target_color
        ]

        # Costo totale per colorare tutte le celle sbagliate
        color_cost = len(to_color) * self.target_color.cost

        # Distanza di Manhattan dalla posizione corrente alla cella sbagliata più vicina, più la distanza di quella cella a start_pos
        if not to_color:
            return abs(pos[0] - self.start_pos[0]) + abs(pos[1] - self.start_pos[1])

        # Distanza di Manhattan tra due posizioni (riga, colonna)
        def mdist(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        # Calcola la distanza minima dalla posizione corrente a una cella sbagliata e da quella cella a start_pos
        min_to_cell = min(mdist(pos, p) for p in to_color)
        # Calcola la distanza minima da una cella sbagliata a start_pos
        min_cell_to_start = min(mdist(p, self.start_pos) for p in to_color)
        travel = min_to_cell + min_cell_to_start

        return color_cost + travel
