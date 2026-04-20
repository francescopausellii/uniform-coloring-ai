import itertools


class Heuristics:
    """
    Collection of heuristics for the UniformColoring problem.
    Adapted from: https://github.com/youness-1/UniformColoring

    Each method takes an AIMA Node and returns an estimated cost h(n).
    The problem instance is required at construction to access start_pos and target_color.
    """

    def __init__(self, problem):
        self.problem = problem

    @staticmethod
    def _mdist(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _wrong_cells(self, grid):
        """Return list of (r, c) that still need to be painted with target_color."""
        p = self.problem
        return [
            (r, c)
            for r in range(p.rows)
            for c in range(p.cols)
            if (r, c) != p.start_pos and grid[r][c] != p.target_color
        ]

    def color(self, node):
        """
        Admissible. Counts remaining cells to paint × target color cost.
        Ignores travel distance entirely — fast but loose lower bound.
        """
        wrong = self._wrong_cells(node.state.grid)
        return len(wrong) * self.problem.target_color.cost

    def color_nearest_distance(self, node):
        """
        Admissible. Coloring cost + distance to nearest wrong cell
        + distance from that cell back to start_pos.
        Equivalent to: min over wrong cells of (dist_to_cell + dist_cell_to_start).
        """
        p = self.problem
        pos = node.state.pos
        wrong = self._wrong_cells(node.state.grid)
        color_cost = len(wrong) * p.target_color.cost

        if not wrong:
            return self._mdist(pos, p.start_pos)

        best = min(
            self._mdist(pos, cell) + self._mdist(cell, p.start_pos)
            for cell in wrong
        )
        return color_cost + best

    def color_nearest_neighbor_distance(self, node):
        """
        NOT admissible (can overestimate). Greedy nearest-neighbor traversal:
        from current position visit each wrong cell by always picking the closest,
        then return to start. Fast and effective in practice.
        """
        p = self.problem
        pos = node.state.pos
        wrong = list(self._wrong_cells(node.state.grid))
        color_cost = len(wrong) * p.target_color.cost

        current = pos
        total_dist = 0
        while wrong:
            nearest = min(wrong, key=lambda cell: self._mdist(current, cell))
            total_dist += self._mdist(current, nearest)
            current = nearest
            wrong.remove(nearest)

        total_dist += self._mdist(current, p.start_pos)
        return color_cost + total_dist

    def ideal(self, node):
        """
        Admissible. Tries ALL permutations of wrong cells to find the minimum
        travel distance (exact TSP solution). Optimal lower bound but
        O(n!) complexity — only practical for small grids or few remaining cells.
        """
        p = self.problem
        pos = node.state.pos
        wrong = self._wrong_cells(node.state.grid)
        color_cost = len(wrong) * p.target_color.cost

        if not wrong:
            return self._mdist(pos, p.start_pos)

        min_dist = None
        for perm in itertools.permutations(wrong):
            dist = self._mdist(pos, perm[0])
            for i in range(len(perm) - 1):
                dist += self._mdist(perm[i], perm[i + 1])
            dist += self._mdist(perm[-1], p.start_pos)

            if min_dist is None or dist < min_dist:
                min_dist = dist

        return color_cost + min_dist
