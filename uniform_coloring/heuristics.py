import itertools

from uniform_coloring.problem import Color


class Heuristics:
    def __init__(self, problem):
        self.problem = problem

    @staticmethod
    def _mdist(a, b):
        """Distanza di Manhattan tra due posizioni (r,c)."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _wrong_cells(self, grid):
        """Celle che non hanno ancora target_color (esclusa start_pos)."""
        p = self.problem
        return [
            (r, c)
            for r in range(p.rows)
            for c in range(p.cols)
            if (r, c) != p.start_pos and grid[r][c] != p.target_color
        ]

    def color(self, node):
        """h = celle_sbagliate × costo_target. Ammissibile, ignora completamente i movimenti."""
        # Somma dei costi per tutte le celle che non sono del target_color e non sono start_pos
        wrong = self._wrong_cells(node.state.grid)
        # Costo totale per colorare tutte le celle sbagliate
        return len(wrong) * self.problem.target_color.cost

    def color_nearest_distance(self, node):
        """
        h = costo colorazione + min(dist(pos, cell) + dist(cell, start)).
        Ammissibile: assume di visitare una sola cella, quindi sottostima sempre.
        """
        p = self.problem
        pos = node.state.pos
        wrong = self._wrong_cells(node.state.grid)
        color_cost = len(wrong) * p.target_color.cost

        # Se non ci sono celle sbagliate, il costo è solo la distanza dalla posizione corrente alla posizione di partenza
        if not wrong:
            return self._mdist(pos, p.start_pos)

        # Altrimenti calcoliamo il costo minimo per visitare una cella sbagliata e tornare alla posizione di partenza
        best = min(
            self._mdist(pos, cell) + self._mdist(cell, p.start_pos) for cell in wrong
        )
        return color_cost + best

    def mst(self, node):
        """
        Lower bound TSP via MST (Prim) su {pos, celle_sbagliate, start}.
        Ammissibile e consistente. Più informativa di color_nearest_distance.
        """
        p = self.problem
        pos = node.state.pos
        wrong = self._wrong_cells(node.state.grid)
        color_cost = len(wrong) * p.target_color.cost

        # Se non ci sono celle sbagliate, il costo è solo la distanza dalla posizione corrente alla posizione di partenza
        if not wrong:
            return self._mdist(pos, p.start_pos)

        points = [pos] + wrong
        if p.start_pos != pos:
            points.append(p.start_pos)

        n = len(points)

        # Prim's MST
        in_tree = [False] * n
        in_tree[0] = True
        edges_weight = 0

        for _ in range(n - 1):
            min_edge = float("inf")
            next_point = -1

            for i in range(n):
                if in_tree[i]:
                    for j in range(n):
                        if not in_tree[j]:
                            dist = self._mdist(points[i], points[j])
                            if dist < min_edge:
                                min_edge = dist
                                next_point = j

            edges_weight += min_edge
            in_tree[next_point] = True

        return color_cost + edges_weight

    def ideal(self, node):
        """
        Tour ottimo esatto via brute-force. Ammissibile per definizione.
        Usare solo su istanze piccole (n ≤ 8 celle sbagliate).
        """
        p = self.problem
        pos = node.state.pos
        wrong = self._wrong_cells(node.state.grid)
        color_cost = len(wrong) * p.target_color.cost

        if not wrong:
            return self._mdist(pos, p.start_pos)

        min_dist = min(
            self._mdist(pos, perm[0])
            + sum(self._mdist(perm[i], perm[i + 1]) for i in range(len(perm) - 1))
            + self._mdist(perm[-1], p.start_pos)
            for perm in itertools.permutations(wrong)
        )
        return color_cost + min_dist
