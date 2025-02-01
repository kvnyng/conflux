import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from stl import mesh


def generate_3d_mesh_from_white_image(
    output_stl_path, image_size=(300, 300), sigma=5, margin=20
):
    """
    Generates a 3D mesh from a white heightmap image.

    Parameters:
        output_stl_path (str): Path where the STL file will be saved.
        image_size (tuple): Size of the generated white image.
        sigma (float): The Gaussian smoothing parameter.
        margin (int): The margin (in pixels) from the edge where smoothing starts.

    Returns:
        None
    """
    # Create a white image
    height_map_image = Image.new("L", image_size, color=255)  # White image

    # Convert to numpy array and normalize
    height_data = np.array(height_map_image) / 255.0

    # Apply Gaussian smoothing
    smoothed_height_data = gaussian_filter(height_data, sigma=sigma)

    # Calculate the average value within the margin
    top_margin_avg = np.mean(smoothed_height_data[:margin, :])
    bottom_margin_avg = np.mean(smoothed_height_data[-margin:, :])
    left_margin_avg = np.mean(smoothed_height_data[:, :margin])
    right_margin_avg = np.mean(smoothed_height_data[:, -margin:])

    edge_value = (
        top_margin_avg + bottom_margin_avg + left_margin_avg + right_margin_avg
    ) / 4

    # Smoothly bring the edges of the height map to the average value within the margin
    rows, cols = smoothed_height_data.shape
    for i in range(rows):
        if i < margin or i >= rows - margin:
            factor = min(i / margin, (rows - 1 - i) / margin, 1)
            smoothed_height_data[i, :] = (
                1 - factor
            ) * edge_value + factor * smoothed_height_data[i, :]

    for j in range(cols):
        if j < margin or j >= cols - margin:
            factor = min(j / margin, (cols - 1 - j) / margin, 1)
            smoothed_height_data[:, j] = (
                1 - factor
            ) * edge_value + factor * smoothed_height_data[:, j]

    # Create a grid for the mesh
    x = np.linspace(0, 1, smoothed_height_data.shape[1])
    y = np.linspace(0, 1, smoothed_height_data.shape[0])
    x, y = np.meshgrid(x, y)

    # Prepare vertices and faces for STL
    vertices = []
    faces = []
    for i in range(x.shape[0] - 1):
        for j in range(y.shape[1] - 1):
            # Define the vertices of two triangles for each grid cell
            v0 = [x[i, j], y[i, j], smoothed_height_data[i, j]]
            v1 = [x[i + 1, j], y[i + 1, j], smoothed_height_data[i + 1, j]]
            v2 = [x[i, j + 1], y[i, j + 1], smoothed_height_data[i, j + 1]]
            v3 = [x[i + 1, j + 1], y[i + 1, j + 1], smoothed_height_data[i + 1, j + 1]]

            # Append vertices for the two triangles
            vertices.extend([v0, v1, v2, v3])

            # Triangle 1 (v0, v1, v2)
            faces.append([len(vertices) - 4, len(vertices) - 3, len(vertices) - 2])
            # Triangle 2 (v2, v1, v3)
            faces.append([len(vertices) - 2, len(vertices) - 3, len(vertices) - 1])

    vertices = np.array(vertices)
    faces = np.array(faces)

    # Create the mesh
    terrain_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            terrain_mesh.vectors[i][j] = vertices[f[j], :]

    # Save the mesh to an STL file
    terrain_mesh.save(output_stl_path)


# Example usage
generate_3d_mesh_from_white_image("output.stl")
