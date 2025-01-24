import numpy as np
import trimesh


# Correct absolute path to the STL file
stl_file_path = "/Users/romyaran/Desktop/Hands/Hannah/output_mesh.stl"

# Load the STL file using trimesh
try:
    tile_mesh = trimesh.load(stl_file_path)
    print("STL file loaded successfully!")
except Exception as e:
    print(f"Error loading STL file: {e}")


# Reload the uploaded STL file
stl_file_path = "/Users/romyaran/Desktop/Hands/Hannah/output_mesh.stl"
tile_mesh = trimesh.load(stl_file_path)

# Sphere and tiling parameters
R = 1  # Radius of the sphere
N = 5  # Total number of tiles (adjusted for manageable size)
M = int(np.sqrt(N))  # Number of latitude bands
N_per_band = int(N / M)  # Number of tiles per latitude band

# Latitude and longitude edges
theta_edges = np.linspace(0, np.pi, M + 1)  # Latitude (0 to pi)
phi_edges = np.linspace(0, 2 * np.pi, N_per_band + 1)  # Longitude (0 to 2pi)


# Function to map vertices to the sphere
def map_to_sphere(vertices, theta_bounds, phi_bounds, R):
    """Maps a flat tile's vertices onto a spherical tile."""
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]

    # Scale x and y to longitude and latitude ranges
    phi = phi_bounds[0] + x * (phi_bounds[1] - phi_bounds[0])
    theta = theta_bounds[0] + y * (theta_bounds[1] - theta_bounds[0])

    # Project onto sphere (preserving z as height for topography)
    new_x = (R + z) * np.sin(theta) * np.cos(phi)
    new_y = (R + z) * np.sin(theta) * np.sin(phi)
    new_z = (R + z) * np.cos(theta)

    return np.column_stack((new_x, new_y, new_z))


# Initialize arrays for the full sphere
all_vertices = []
all_faces = []
face_offset = 0

# Iterate through all tiles on the sphere
for lat_idx in range(len(theta_edges) - 1):
    for lon_idx in range(len(phi_edges) - 1):
        # Get the bounds for the current tile
        theta1, theta2 = theta_edges[lat_idx], theta_edges[lat_idx + 1]
        phi1, phi2 = phi_edges[lon_idx], phi_edges[lon_idx + 1]

        # Map the vertices of the tile mesh to this spherical region
        mapped_vertices = map_to_sphere(
            tile_mesh.vertices, (theta1, theta2), (phi1, phi2), R
        )

        # Append the mapped vertices and adjusted faces
        all_vertices.append(mapped_vertices)
        all_faces.append(tile_mesh.faces + face_offset)

        # Update face offset for the next tile
        face_offset += len(mapped_vertices)

# Combine all vertices and faces
all_vertices = np.vstack(all_vertices)
all_faces = np.vstack(all_faces)

# Create the full tiled sphere mesh
full_tiled_sphere = trimesh.Trimesh(vertices=all_vertices, faces=all_faces)

# Save the tiled sphere to an STL file
tiled_sphere_path = "/Users/romyaran/Desktop/tiled_sphere_N100.stl"
full_tiled_sphere.export(tiled_sphere_path)

tiled_sphere_path
