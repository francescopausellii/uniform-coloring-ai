from enum import Enum
from aima.search import Problem


class Color(Enum):
    BLUE = ('B', 1)
    YELLOW = ('Y', 2)
    GREEN = ('G', 3)
    EMPTY = ('T', 0)  # Placeholder for the initial position of the head (T)

    def __init__(self, symbol, cost):
        self.symbol = symbol
        self.cost = cost

    # This allows to compare colors based on their cost (which is useful for UCS)
    def __lt__(self, other):
        if isinstance(other, Color):
            return self.cost < other.cost
        return NotImplemented


class Move(Enum):
    NORTH = (-1, 0)
    SOUTH = (1, 0)
    EAST = (0, 1)
    WEST = (0, -1)


class State:
    def __init__(self, grid, pos):
        self.grid = grid
        self.pos = pos
        symbols = ','.join(cell.symbol for row in grid for cell in row)
        self.id = f"{pos[0]},{pos[1]}:{symbols}"

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    def __lt__(self, other):
        return self.id < other.id


class UniformColoring(Problem):
    def __init__(self, grid_matrix):
        """
        Initialize the problem from a matrix (list of lists).
        Example of input:
        grid_matrix = [
            ['G', 'T', 'G', 'B'],
            ['G', 'Y', 'G', 'B']
        ]
        """
        self.rows = len(grid_matrix)
        self.cols = len(grid_matrix[0])
        self.start_pos = None

        # Create a mapping from symbols to colors
        symbol_to_color = {c.symbol: c for c in Color if c != Color.EMPTY}

        # Build the initial grid and find the head (T)
        initial_grid = []
        for r in range(self.rows):
            row_colors = []
            for c in range(self.cols):
                char = grid_matrix[r][c]
                if grid_matrix[r][c] == 'T':
                    self.start_pos = (r, c)
                    # 'T' = Uncolored (starting position is not colored)
                    row_colors.append(Color.EMPTY)
                else:
                    row_colors.append(symbol_to_color[char])
            initial_grid.append(tuple(row_colors))

        # Determine optimal target color (minimizes total recoloring cost)
        non_start = [(r, c) for r in range(self.rows) for c in range(self.cols)
                     if (r, c) != self.start_pos]
        self.target_color = min(
            [Color.BLUE, Color.YELLOW, Color.GREEN],
            key=lambda tc: sum(tc.cost for r, c in non_start
                               if initial_grid[r][c] != tc)
        )

        # The state is a State object with immutable grid and position
        initial_state = State(tuple(initial_grid), self.start_pos)

        super().__init__(initial_state)

    def actions(self, state):
        """Return the legal actions in a given state."""
        grid, pos = state.grid, state.pos
        r, c = pos
        possible_actions = []

        # 1. Actions (N, S, E, W) without leaving the grid
        for move in Move:
            dr, dc = move.value
            new_r, new_c = r + dr, c + dc
            if 0 <= new_r < self.rows and 0 <= new_c < self.cols:
                possible_actions.append(move)

        # 2. Color current cell with target color only (if it needs recoloring)
        # Skips start_pos (EMPTY cell ignored in goal_test) and already-correct cells
        if (r, c) != self.start_pos and grid[r][c] != self.target_color:
            possible_actions.append(self.target_color)

        return possible_actions

    def result(self, state, action):
        """Return the resulting state from executing a given action."""
        grid, pos = state.grid, state.pos

        # Resolution of movements
        if isinstance(action, Move):
            dr, dc = action.value
            return State(grid, (pos[0] + dr, pos[1] + dc))

        # Resolution of coloring
        if isinstance(action, Color):
            # Convert the grid to a mutable structure (list of lists) to modify it
            new_grid = [list(row) for row in grid]
            new_grid[pos[0]][pos[1]] = action
            # Reconvert the grid to an immutable structure (tuple of tuples) for the new state
            return State(tuple(tuple(row) for row in new_grid), pos)

    def path_cost(self, c, state1, action, state2):
        """Return the cost of the path c + the cost of the action."""
        if isinstance(action, Move):
            return c + 1
        if isinstance(action, Color):
            return c + action.cost
        return c  # pragma: no cover

    def goal_test(self, state):
        """Return True if the current state is a goal state."""
        grid, pos = state.grid, state.pos

        # 1. The head must be in its starting position
        if pos != self.start_pos:
            return False

        # 2. All cells must have the same color (ignoring the initial cell where T is located)
        first_color = None
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) == self.start_pos:
                    continue

                cell_color = grid[r][c]
                if cell_color == Color.EMPTY:
                    return False  # Not yet colored

                if first_color is None:
                    first_color = cell_color
                elif cell_color != first_color:
                    return False
        # If there is only one color in the grid, we have a uniform coloring, otherwise we do not
        return True

    def h(self, node):
        """
        Admissible heuristic: estimates minimum cost to reach goal.
        Combines coloring cost + nearest-neighbor lower bound on travel distance.
        """
        grid, pos = node.state.grid, node.state.pos

        # Cells that still need to be painted with target_color
        to_color = [(r, c) for r in range(self.rows) for c in range(self.cols)
                    if (r, c) != self.start_pos and grid[r][c] != self.target_color]

        color_cost = len(to_color) * self.target_color.cost

        if not to_color:
            return abs(pos[0] - self.start_pos[0]) + abs(pos[1] - self.start_pos[1])

        # Lower bound on travel: reach nearest uncolored cell, then return to start from farthest
        def mdist(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        min_to_cell = min(mdist(pos, p) for p in to_color)
        min_cell_to_start = min(mdist(p, self.start_pos) for p in to_color)
        travel = min_to_cell + min_cell_to_start

        return color_cost + travel
