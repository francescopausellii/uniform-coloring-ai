from collections import deque
import heapq
from aima.search import Node


def breadth_first_graph_search(problem):
    """Breadth-first graph search with O(1) frontier lookup."""
    node = Node(problem.initial)
    if problem.goal_test(node.state):
        return node

    frontier = deque([node])
    frontier_ids = {node.state.id}  # Set for O(1) lookup
    explored = set()

    while frontier:
        node = frontier.popleft()
        explored.add(node.state.id)

        # Expand node: generate all child states reachable by valid actions
        for child in node.expand(problem):
            sid = child.state.id
            # Only process if state not yet explored or in frontier
            if sid not in explored and sid not in frontier_ids:
                if problem.goal_test(child.state):
                    return child
                frontier.append(child)
                frontier_ids.add(sid)

    return None


def uniform_cost_search(problem):
    """Uniform cost search with O(1) frontier lookup."""
    node = Node(problem.initial)
    # Heap: (path_cost, node_id, node). node_id breaks ties to avoid Node comparison.
    frontier = [(0, id(node), node)]
    frontier_ids = {node.state.id}  # Set for O(1) lookup
    explored = set()

    while frontier:
        # Pop node with lowest path cost from heap
        _, _, node = heapq.heappop(frontier)

        # Skip if already explored (handles duplicate states from heap)
        if node.state.id in explored:
            continue

        if problem.goal_test(node.state):
            return node

        explored.add(node.state.id)

        # Expand node: generate all child states reachable by valid actions
        for child in node.expand(problem):
            sid = child.state.id
            # Only process if state not yet explored or in frontier
            if sid not in explored and sid not in frontier_ids:
                heapq.heappush(frontier, (child.path_cost, id(child), child))
                frontier_ids.add(sid)

    return None


def astar_search(problem, h=None):
    """A* search with O(1) frontier lookup."""
    h = h or problem.h
    node = Node(problem.initial)
    f0 = node.path_cost + h(node)
    # Heap: (f-value, node_id, node). node_id breaks ties to avoid Node comparison.
    frontier = [(f0, id(node), node)]
    frontier_ids = {node.state.id}  # Set for O(1) lookup
    explored = set()

    while frontier:
        # Pop node with lowest f-value (g + h) from heap
        _, _, node = heapq.heappop(frontier)

        # Skip if already explored (handles duplicate states from heap)
        if node.state.id in explored:
            continue

        if problem.goal_test(node.state):
            return node

        explored.add(node.state.id)

        # Expand node: generate all child states reachable by valid actions
        for child in node.expand(problem):
            sid = child.state.id
            # Only process if state not yet explored or in frontier
            if sid not in explored and sid not in frontier_ids:
                f = child.path_cost + h(child)
                heapq.heappush(frontier, (f, id(child), child))
                frontier_ids.add(sid)

    return None
