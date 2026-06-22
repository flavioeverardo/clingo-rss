from . import graph
from . import distance
from . import colors as colours
import matplotlib.pyplot as plt
import numpy as np
import os

def build_colors_solution(colors, current_solution, number, cost, size, approach):
    
    # Normalize RGB values to [0, 1] for matplotlib
    colors_normalized = [(r / 255, g / 255, b / 255) for r, g, b in colors]

    atoms = current_solution.symbols(shown=True)
    colors_dict = {}
    for atom in atoms:
        if len(atom.arguments) == 2:
            cluster  = int(str(atom.arguments[0]))
            color_id = int(str(atom.arguments[1]))
            color = colors_normalized[color_id - 1]
            colors_dict[cluster] = color 

    # Create the plot
    fig, ax = plt.subplots(figsize=(6, 6))

    # Draw a NxN grid
    grid_size = size
    for index, color in colors_dict.items():
        row = (index - 1) // grid_size  # Calculate row (zero-indexed)
        col = (index - 1) % grid_size  # Calculate column (zero-indexed)
        rect = plt.Rectangle((col, grid_size - row - 1), 1, 1, color=color)  # Draw rectangle
        ax.add_patch(rect)

    # Set axis limits and turn off the axis
    ax.set_xlim(0, grid_size)
    ax.set_ylim(0, grid_size)
    ax.set_aspect('equal')
    ax.axis('off')

    # Check if the directory exists
    out_dir = "results/%s_%sx%s"%(approach, grid_size, grid_size)
    if not os.path.exists(out_dir):
        # Create the directory
        os.makedirs(out_dir)
        
    # Save the plot as an image
    output_filename = "%s/color_grid_%s_%s.png"%(out_dir, number, cost)
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')

    # Optionally, close the figure to free resources
    plt.close(fig)

    print(f"Plot saved as '{output_filename}'")
    

def build_colors_test_instance(n_colors):
    # Generate N random colors
    print("Number of colors:", n_colors)
    color_solutions = []
    colors = colours.generate_colors_space(n_colors)
    for i, color in enumerate(colors):
        print(f" Color {i + 1}: {color}")

        # Generate sequences
        sequence_r = [f"color(r,{str(num)})." for num in range(1, color[0] + 1)] # From 1 to R
        sequence_g = [f"color(g,{str(num)})." for num in range(1, color[1] + 1)] # From 1 to G
        sequence_b = [f"color(b,{str(num)})." for num in range(1, color[2] + 1)] # From 1 to B

        colors_list = sequence_r + sequence_g + sequence_b
        #print(colors_list)
        #print(len(colors_list))
        #print()
        color_solutions.append(colors_list)

    return colors, color_solutions

def build_instance(answer_sets, k, size, add_diagonals, add_distances, add_nodes, add_edges):
    print("Calculating distances...")
    instance = ""
    if add_distances:
        distancesText = distance.calculate_distances(answer_sets, k)
        instance += distancesText

    print("Building the map...")

    my_graph = graph.Graph((size,size), add_diagonals)
    my_graph = my_graph.nodes

    ## Set the constant
    instance += "%% Set the size of the map\n"
    instance += "size(%s).\n"%size
    instance += ""

    map = {}

    ## Get nodes
    instance += "%% Answer sets to fill the map.\n"
    for i in range(len(answer_sets)):
        #if add_nodes:
        instance += "answer_set(%s).\n"%(i+1)

    instance += "\n"
    instance += "%% Nodes in the map\n"
    node_id = 1
    for key, value in my_graph.items():
        if add_nodes:
            instance += "node(%s).\n"%(node_id)
        map[key] = node_id
        node_id+=1

    instance += "\n"
    instance += "%% Bidirectional edges from the map.\n"

    ## Get edges
    grid_edges = []
    for key, value in map.items():
        for node in my_graph[key]:
            if(value < map[node]):
                if add_edges:
                    instance += "edge(%s,%s).\n"%(value, map[node])
                ## Get the edges to calculate the distance factor
                grid_edges.append([value-1,map[node]-1])

    
    return instance, grid_edges

def get_numbers_sequence(n, inf, sup):
    output = []
    if n > 1:
        continuous_difference = (sup-inf)/n
        initial = inf
        final = sup

        output.append(initial)
        for _ in range(n):
            output.append(initial + continuous_difference)
            initial += continuous_difference
    
        return output
    else:
        return None

def print_squares(squares):
    for N, square in squares.items():
        print("%sx%s square edges:"%(N, N))
        print(square)

def extract_square_edges(edges, start_node, size, N):
    """
    Extract edges forming a square from a grid graph.

    Parameters:
    - edges: List of all edges in the graph (e.g., [[1, 2], [1, 6], ...]).
    - start_node: Top-left node of the square (e.g., 1).
    - size: Size of the square (e.g., 2 for 2x2).

    Returns:
    - List of edges in the square.
    """
    # Generate all nodes in the square
    square_nodes = []
    for i in range(size):
        for j in range(size):
            square_nodes.append(start_node + i * N + j)

    # Determine edges within the square
    square_edges = [
        edge for edge in edges
        if edge[0] in square_nodes and edge[1] in square_nodes
    ]

    return square_edges
