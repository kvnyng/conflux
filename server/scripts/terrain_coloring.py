import numpy as np
from stl import mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# Load the STL file
file_path = "./data/planets/KevinYang_fe5e59a6d3699fd1af0470b1fa5773610_planet.stl"  # Replace with your STL file path
your_mesh = mesh.Mesh.from_file(file_path)

# Extract vertices
vertices = your_mesh.vectors.reshape(-1, 3)

# Calculate the center of the model (centroid of all vertices)
center = np.mean(vertices, axis=0)

# Calculate radial distances from the center for each vertex
distances = np.linalg.norm(vertices - center, axis=1)

# Define geographic-like color bands based on radial distances
terrain_colors = {
    "deep_ocean": "#0000ff",  # Blue
    "shallow_water": "#00bfff",  # Light Blue
    "shore": "#ffff00",  # Yellow
    "lowland": "#008000",  # Green
    "highland": "#a0522d",  # Brown
    "mountain": "#ffffff",  # White
}
# Define distance cut-offs for each terrain
cutoffs = [0.2, 0.4, 0.6, 0.8, 1.0]  # Relative to max distance
max_distance = np.max(distances)

# Normalize distances and assign colors
colors = []
for dist in distances:
    normalized = dist / max_distance
    if normalized <= cutoffs[0]:
        colors.append(terrain_colors["deep_ocean"])
    elif normalized <= cutoffs[1]:
        colors.append(terrain_colors["shallow_water"])
    elif normalized <= cutoffs[2]:
        colors.append(terrain_colors["shore"])
    elif normalized <= cutoffs[3]:
        colors.append(terrain_colors["lowland"])
    elif normalized <= cutoffs[4]:
        colors.append(terrain_colors["highland"])
    else:
        colors.append(terrain_colors["mountain"])

# Visualize the STL with colors
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")

# Create a Poly3DCollection to add color to each triangle face
for i, vector in enumerate(your_mesh.vectors):
    poly = Poly3DCollection([vector])
    poly.set_facecolor(colors[i])
    poly.set_edgecolor("black")
    ax.add_collection3d(poly)

# Adjust the plot
ax.auto_scale_xyz(vertices[:, 0], vertices[:, 1], vertices[:, 2])

# Save the plot as an image
output_image_path = "output_image.png"  # Replace with your desired output path
plt.savefig(output_image_path, dpi=300, bbox_inches="tight")
plt.close(fig)  # Close the figure to free memory
