from aima.search import Problem


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

        # Build the initial grid and find the head (T)
        initial_grid = []
        for r in range(self.rows):
            row_colors = []
            for c in range(self.cols):
                if grid_matrix[r][c] == 'T':
                    self.start_pos = (r, c)
                    # 'U' = Uncolored (starting position is not colored)
                    row_colors.append('U')
                else:
                    row_colors.append(grid_matrix[r][c])
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
        if r > 0:
            possible_actions.append('Nord')
        if r < self.rows - 1:
            possible_actions.append('Sud')
        if c < self.cols - 1:
            possible_actions.append('East')
        if c > 0:
            possible_actions.append('West')

        # 2. Actions for coloring (col-B, col-Y, col-G)
        # It makes sense to color only if the cell has a different color from the one we want to apply
        current_color = grid[r][c]
        for color in ['B', 'Y', 'G']:
            if current_color != color:
                possible_actions.append(f'col-{color}')

        return possible_actions

    def result(self, state, action):
        """Return the resulting state from executing a given action."""
        grid, pos = state
        r, c = pos

        # Resolution of movements
        if action == 'Nord':
            return (grid, (r - 1, c))
        if action == 'Sud':
            return (grid, (r + 1, c))
        if action == 'East':
            return (grid, (r, c + 1))
        if action == 'West':
            return (grid, (r, c - 1))

        # Resolution of coloring
        if action.startswith('col-'):
            new_color = action.split('-')[1]
            # Convert the grid to a mutable structure (list of lists) to modify it
            new_grid = list(list(row) for row in grid)
            new_grid[r][c] = new_color
            # Reconvert the grid to an immutable structure (tuple of tuples) for the new state
            new_grid_tuple = tuple(tuple(row) for row in new_grid)
            return (new_grid_tuple, pos)

    def path_cost(self, c, action):
        """Return the cost of the path c + the cost of the action."""
        if action in ['Nord', 'Sud', 'East', 'West']:
            return c + 1
        if action == 'col-B':
            return c + 1
        if action == 'col-Y':
            return c + 2
        if action == 'col-G':
            return c + 3
        return c

    def goal_test(self, state):
        """Return True if the current state is a goal state."""
        grid, pos = state

        # 1. The head must be in its starting position
        if pos != self.start_pos:
            return False

        # 2. All cells must have the same color (ignoring the initial cell where T is located)
        colors_found = set()
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) != self.start_pos:
                    colors_found.add(grid[r][c])

        # If there is only one color in the set (e.g., only 'G'), we have a uniform coloring, otherwise we do not
        return len(colors_found) == 1
