from collections import deque
import heapq
from aima.search import Node


def breadth_first_graph_search(problem):
    """
    BFS su grafo. Minimizza il numero di passi, non il costo totale.
    Se i costi non sono uniformi, usare UCS.
    """
    node = Node(problem.initial)

    if problem.goal_test(node.state):
        return node

    frontier = deque([node])
    frontier_ids = {node.state.id}
    explored = set()

    while frontier:
        node = frontier.popleft()
        frontier_ids.discard(node.state.id)
        explored.add(node.state.id)

        for child in node.expand(problem):
            sid = child.state.id

            if sid not in explored and sid not in frontier_ids:
                # goal test al momento della generazione
                if problem.goal_test(child.state):
                    return child

                frontier.append(child)
                frontier_ids.add(sid)

    return None


def uniform_cost_search(problem):
    """
    UCS: espande per path_cost crescente. Ottimale.

    Usa lazy deletion perché l'heap di Python non supporta aggiornamento di priorità:
    i duplicati vengono inseriti e scartati all'estrazione se lo stato è già esplorato.
    """
    node = Node(problem.initial)

    # (path_cost, tiebreaker, nodo) — tiebreaker evita confronti diretti tra Node
    frontier = [(0, id(node), node)]
    explored = set()

    while frontier:
        _, _, node = heapq.heappop(frontier)

        # lazy deletion: salta duplicati già esplorati con costo minore
        if node.state.id in explored:
            continue

        if problem.goal_test(node.state):
            return node

        explored.add(node.state.id)

        for child in node.expand(problem):
            if child.state.id not in explored:
                heapq.heappush(frontier, (child.path_cost, id(child), child))

    return None


def astar_search(problem, h=None):
    """
    A*: espande per f(n) = g(n) + h(n). Ottimale se h è ammissibile.
    Stesso pattern lazy deletion di UCS.
    """
    h = h or problem.h

    node = Node(problem.initial)
    frontier = [(node.path_cost + h(node), id(node), node)]
    explored = set()

    while frontier:
        _, _, node = heapq.heappop(frontier)

        # lazy deletion
        if node.state.id in explored:
            continue

        if problem.goal_test(node.state):
            return node

        explored.add(node.state.id)

        for child in node.expand(problem):
            if child.state.id not in explored:
                f = child.path_cost + h(child)
                heapq.heappush(frontier, (f, id(child), child))

    return None
