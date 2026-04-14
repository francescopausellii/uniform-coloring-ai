def print_grid(grid, position=None):
    """Pretty print the grid with nice formatting."""
    r, c = position if position else (0, 0)
    for i, row in enumerate(grid):
        # Handle both enum and string representations of colors
        row_str = " | ".join(
            [f"{getattr(color, 'symbol', color):^2}" for color in row])
        marker = " <- HEAD" if i == r else ""
        print(f"  {row_str}{marker}")


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def print_solution_results(solution, alg_name):
    """Helper to print solution details."""
    if solution:
        path = solution.solution()
        print(f"--- Result {alg_name} ---")
        print(f"✓ Solution found in {len(path)} steps")
        print(f"Total cost = {solution.path_cost}")
        print(f"\nAction sequence:")
        for i, step in enumerate(path, 1):
            print(f"  {i}. {step}")
    else:
        print(f"✗ No solution found with {alg_name}")