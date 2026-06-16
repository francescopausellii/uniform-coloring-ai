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
        node.nodes_expanded = 0
        return node

    frontier = deque([node])
    frontier_ids = {node.state.id}
    explored = set()
    nodes_expanded = 0

    while frontier:
        node = frontier.popleft()
        frontier_ids.discard(node.state.id)
        explored.add(node.state.id)
        nodes_expanded += 1

        for child in node.expand(problem):
            sid = child.state.id

            if sid not in explored and sid not in frontier_ids:
                # goal test al momento della generazione
                if problem.goal_test(child.state):
                    child.nodes_expanded = nodes_expanded
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

    # (path_cost, counter, nodo) — counter monotono garantisce determinismo sui pareggi
    counter = 0
    frontier = [(0, counter, node)]
    explored = set()
    nodes_expanded = 0

    while frontier:
        _, _, node = heapq.heappop(frontier)

        # lazy deletion: salta duplicati già esplorati con costo minore
        if node.state.id in explored:
            continue

        if problem.goal_test(node.state):
            node.nodes_expanded = nodes_expanded
            return node

        explored.add(node.state.id)
        nodes_expanded += 1

        for child in node.expand(problem):
            if child.state.id not in explored:
                counter += 1
                heapq.heappush(frontier, (child.path_cost, counter, child))

    return None


def astar_search(problem, h=None):
    """
    A*: espande per f(n) = g(n) + h(n). Ottimale se h è ammissibile.
    Stesso pattern lazy deletion di UCS.
    """
    h = h or problem.h

    node = Node(problem.initial)
    counter = 0
    frontier = [(node.path_cost + h(node), counter, node)]
    explored = set()
    nodes_expanded = 0

    while frontier:
        _, _, node = heapq.heappop(frontier)

        # lazy deletion
        if node.state.id in explored:
            continue

        if problem.goal_test(node.state):
            node.nodes_expanded = nodes_expanded
            return node

        explored.add(node.state.id)
        nodes_expanded += 1

        for child in node.expand(problem):
            if child.state.id not in explored:
                counter += 1
                f = child.path_cost + h(child)
                heapq.heappush(frontier, (f, counter, child))

    return None