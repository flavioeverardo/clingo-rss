import random
import numpy as np
import math


# Function to interpolate colors
def interpolate_color(c1, c2, t):
    return (1 - t) * c1 + t * c2

def generate_colors_space(N):
    colors = []

    # Define the 4 corner colors
    ## Rainbow pallet
    TL = np.array([  1, 255, 245])  # Top-left
    TR = np.array([125,  64, 255])  # Top-right
    BL = np.array([255, 209,  37])  # Bottom-left
    BR = np.array([253,   1, 116])  # Bottom-right

    ## Pink and blue pallet
    #TL = np.array([209,111,136])  # Top-left
    #TR = np.array([129, 90,158])  # Top-right
    #BL = np.array([230,230,248])  # Bottom-left
    #BR = np.array([123,204,248])  # Bottom-right

    # Generate a NxN grid of colors
    grid_size = int(math.sqrt(N))
    colors = []

    for i in range(grid_size):
        t_y = i / (grid_size - 1)  # Vertical interpolation factor
        for j in range(grid_size):
            t_x = j / (grid_size - 1)  # Horizontal interpolation factor

            # Interpolate between the corners
            top_color = interpolate_color(TL, TR, t_x)  # Top edge
            bottom_color = interpolate_color(BL, BR, t_x)  # Bottom edge
            color = interpolate_color(top_color, bottom_color, t_y)  # Middle point
            colors.append(color.astype(int).tolist())

    return colors

