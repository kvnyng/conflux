import numpy as np
import trimesh


def map_to_sphere(vertices, theta_bounds, phi_bounds, R):
    """
    Maps a flat tile's vertices onto a spherical tile.

    Parameters:
        vertices (numpy.ndarray): Array of vertices to be mapped.
        theta_bounds (tuple): Latitude bounds (theta_min, theta_max).
        phi_bounds (tuple): Longitude bounds (phi_min, phi_max).
        R (float): Radius of the sphere.

    Returns:
        numpy.ndarray: Array of vertices mapped onto the spherical tile.
    """
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]

    # Scale x and y to longitude and latitude ranges
    phi = phi_bounds[0] + x * (phi_bounds[1] - phi_bounds[0])
    theta = theta_bounds[0] + y * (theta_bounds[1] - theta_bounds[0])

    # Project onto sphere (preserving z as height for topography)
    new_x = (R + z) * np.sin(theta) * np.cos(phi)
    new_y = (R + z) * np.sin(theta) * np.sin(phi)
    new_z = (R + z) * np.cos(theta)

    return np.column_stack((new_x, new_y, new_z))


def create_tiled_sphere(input_stl_path, output_stl_path, R=1, N=5):
    """
    Creates a tiled sphere by mapping flat tiles onto a spherical surface.

    Parameters:
        input_stl_path (str): Path to the input STL file.
        output_stl_path (str): Path to save the output STL file.
        R (float): Radius of the sphere.
        N (int): Total number of tiles.

    Returns:
        None
    """
    # Load the STL file
    try:
        tile_mesh = trimesh.load(input_stl_path)
        print("STL file loaded successfully!")
    except Exception as e:
        print(f"Error loading STL file: {e}")
        return

    # Compute tiling parameters
    M = int(np.sqrt(N))  # Number of latitude bands
    N_per_band = int(N / M)  # Number of tiles per latitude band
    theta_edges = np.linspace(0, np.pi, M + 1)  # Latitude edges
    phi_edges = np.linspace(0, 2 * np.pi, N_per_band + 1)  # Longitude edges

    # Initialize arrays for the full sphere
    all_vertices = []
    all_faces = []
    face_offset = 0

    # Map each tile onto the spherical surface
    for lat_idx in range(len(theta_edges) - 1):
        for lon_idx in range(len(phi_edges) - 1):
            # Bounds for the current tile
            theta_bounds = (theta_edges[lat_idx], theta_edges[lat_idx + 1])
            phi_bounds = (phi_edges[lon_idx], phi_edges[lon_idx + 1])

            # Map vertices to spherical tile
            mapped_vertices = map_to_sphere(
                tile_mesh.vertices, theta_bounds, phi_bounds, R
            )

            # Append mapped vertices and adjusted faces
            all_vertices.append(mapped_vertices)
            all_faces.append(tile_mesh.faces + face_offset)

            # Update face offset
            face_offset += len(mapped_vertices)

    # Combine all vertices and faces into a single mesh
    all_vertices = np.vstack(all_vertices)
    all_faces = np.vstack(all_faces)
    tiled_sphere_mesh = trimesh.Trimesh(vertices=all_vertices, faces=all_faces)

    # Save the tiled sphere mesh to an STL file
    tiled_sphere_mesh.export(output_stl_path)
    print(f"Tiled sphere saved to {output_stl_path}")


if __name__ == "__main__":
    input_stl_path = (
        "./data/landscapes/IdaChen_a5a853539942fd681ed835dfc305b4b8_landscapes.stl"
    )
    output_stl_path = (
        "./data/planets/KevinYang_fe5e59a6d3699fd1af0470b1fa5773610_planet.stl"
    )
    create_tiled_sphere(input_stl_path, output_stl_path, R=2, N=50)
