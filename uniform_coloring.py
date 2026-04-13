from enum import Enum
from aima.search import Problem


class Color(Enum):
    BLUE = ('B', 1)
    YELLOW = ('Y', 2)
    GREEN = ('G', 3)
    EMPTY = ('U', 0)  # Placeholder for the initial position of the head (T)

    def __init__(self, symbol, cost):
        self.symbol = symbol
        self.cost = cost


class Move(Enum):
    NORTH = (-1, 0)
    SOUTH = (1, 0)
    EAST = (0, 1)
    WEST = (0, -1)


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
                    # 'U' = Uncolored (starting position is not colored)
                    row_colors.append(Color.EMPTY)
                else:
                    row_colors.append(symbol_to_color[char])
            initial_grid.append(tuple(row_colors))

        # The state must be immutable: (colored_grid, head_position)
        initial_state = (tuple(initial_grid), self.start_pos)

        super().__init__(initial_state)

    def actions(self, state):
        """Return the legal actions in a given state."""
        grid, pos = state
        r, c = pos
        possible_actions = []

        # 1. Actions (N, S, E, W) without leaving the grid
        for move in Move:
            dr, dc = move.value
            new_r, new_c = r + dr, c + dc
            if 0 <= new_r < self.rows and 0 <= new_c < self.cols:
                possible_actions.append(move)

        # 2. Actions for coloring (col-B, col-Y, col-G)
        # It makes sense to color only if the cell has a different color from the one we want to apply
        current_color = grid[r][c]
        for color in [Color.BLUE, Color.YELLOW, Color.GREEN]:
            if current_color != color:
                possible_actions.append(color)

        return possible_actions

    def result(self, state, action):
        """Return the resulting state from executing a given action."""
        grid, pos = state
        r, c = pos

        # Resolution of movements
        if isinstance(action, Move):
            dr, dc = action.value
            return (grid, (pos[0] + dr, pos[1] + dc))

        # Resolution of coloring
        if isinstance(action, Color):
            # Convert the grid to a mutable structure (list of lists) to modify it
            new_grid = [list(row) for row in grid]
            new_grid[pos[0]][pos[1]] = action
            # Reconvert the grid to an immutable structure (tuple of tuples) for the new state
            return (tuple(tuple(row) for row in new_grid), pos)

    def path_cost(self, c, action):
        """Return the cost of the path c + the cost of the action."""
        if isinstance(action, Move):
            return c + 1
        if isinstance(action, Color):
            return c + action.cost
        return c

    def goal_test(self, state):
        """Return True if the current state is a goal state."""
        grid, pos = state

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
