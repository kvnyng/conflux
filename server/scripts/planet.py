import json
import numpy as np
import trimesh
from pathlib import Path


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


def project_uv_to_sphere(
    uv_fabric: trimesh.Trimesh, radius: float, rows: int, cols: int
) -> trimesh.Trimesh:
    """Projects the UV fabric into a sphere, keeping track of each tile's location."""
    tile_width = 1.0 / cols
    tile_height = 1.0 / rows

    theta_edges = np.linspace(0, np.pi, rows + 1)  # Latitude (0 to pi)
    phi_edges = np.linspace(0, 2 * np.pi, cols + 1)  # Longitude (0 to 2pi)

    all_vertices = []
    all_faces = []
    face_offset = 0

    # Iterate through each tile's corresponding grid position
    for row in range(rows):
        for col in range(cols):
            # Get bounds for the current tile in spherical coordinates
            theta1, theta2 = theta_edges[row], theta_edges[row + 1]
            phi1, phi2 = phi_edges[col], phi_edges[col + 1]

            # Determine which vertices and faces belong to this tile
            mask = (
                (uv_fabric.vertices[:, 0] >= col * tile_width)
                & (uv_fabric.vertices[:, 0] < (col + 1) * tile_width)
                & (uv_fabric.vertices[:, 1] >= row * tile_height)
                & (uv_fabric.vertices[:, 1] < (row + 1) * tile_height)
            )

            tile_vertices = uv_fabric.vertices[mask]
            tile_faces = uv_fabric.faces[np.all(mask[uv_fabric.faces], axis=1)]

            if tile_vertices.size == 0 or tile_faces.size == 0:
                continue  # Skip empty tiles

            # Reindex faces to match the current tile's vertex subset
            unique_indices, new_indices = np.unique(tile_faces, return_inverse=True)
            tile_vertices = tile_vertices[unique_indices]
            tile_faces = new_indices.reshape(tile_faces.shape)

            # Map the vertices of this tile to the spherical region
            mapped_vertices = map_to_sphere(
                tile_vertices, (theta1, theta2), (phi1, phi2), radius
            )

            # Append mapped vertices and adjust faces accordingly
            all_vertices.append(mapped_vertices)
            all_faces.append(tile_faces + face_offset)

            # Update face offset for the next tile
            face_offset += len(mapped_vertices)

    # Combine all vertices and faces into a single mesh
    spherical_mesh = trimesh.Trimesh(
        vertices=np.vstack(all_vertices), faces=np.vstack(all_faces)
    )
    return spherical_mesh


def create_uv_mapped_sphere(
    json_file_path: Path,
    output_uv_path: Path,
    output_sphere_path: Path,
    radius: float,
    smoothing_iterations: int = 10,
):
    """Creates a UV fabric of tiles, smoothens it, and projects it into a sphere."""
    # Load JSON configuration
    try:
        with open(json_file_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        raise ValueError(f"Error loading JSON file: {e}")

    # Extract parameters from JSON
    rows = config.get("rows", 1)
    cols = config.get("cols", 1)
    num_tiles = rows * cols
    tiles = config.get("tiles", {})

    if not tiles:
        raise ValueError("No tile data found in the JSON file.")

    # Step 1: Generate UV fabric
    uv_fabric = generate_uv_fabric(tiles, num_tiles, rows, cols)

    # Save the UV fabric
    uv_fabric.export(str(output_uv_path))
    print(f"UV fabric saved to {output_uv_path}")

    # Step 2: Project UV fabric to sphere
    spherical_mesh = project_uv_to_sphere(uv_fabric, radius, rows, cols)

    # Save the spherical projection
    spherical_mesh.export(str(output_sphere_path))
    print(f"Spherical projection saved to {output_sphere_path}")


def generate_uv_fabric(
    tiles: dict, num_tiles: int, rows: int, cols: int, margin: float = 20.0
) -> trimesh.Trimesh:
    """Generates a UV fabric grid of tiles based on their configuration in the JSON file."""
    tile_width = 1.0 / cols
    tile_height = 1.0 / rows

    all_vertices = []
    all_faces = []
    face_offset = 0

    # A dictionary to track vertex connections for smoothing
    vertex_map = {}

    # Iterate through tiles and calculate their row and column based on index
    for tile_index, tile_data in tiles.items():
        tile_path = tile_data.get("path")
        try:
            tile_mesh = trimesh.load(tile_path)
            print(f"Tile {tile_index} loaded successfully from {tile_path}.")
        except Exception as e:
            raise ValueError(f"Error loading STL file for tile {tile_index}: {e}")

        # Calculate row and column for the tile
        tile_index = int(tile_index)
        row = tile_index // cols
        col = tile_index % cols

        # Offset and transform tile vertices to the grid location
        tile_offset_x = col * tile_width
        tile_offset_y = row * tile_height

        tile_vertices = tile_mesh.vertices.copy()
        tile_vertices[:, 0] = tile_vertices[:, 0] * tile_width + tile_offset_x
        tile_vertices[:, 1] = tile_vertices[:, 1] * tile_height + tile_offset_y

        # Smooth vertices with adjacent tiles within a margin
        for i, vertex in enumerate(tile_vertices):
            key = tuple(vertex.round(decimals=6))  # Round for consistent matching
            if key in vertex_map:
                # Only smooth if the vertex is within the margin of the edge
                distance = np.linalg.norm(vertex - vertex_map[key])
                if distance <= margin:
                    tile_vertices[i] = (tile_vertices[i] + vertex_map[key]) / 2
            vertex_map[key] = tile_vertices[i]

        # Append transformed vertices and faces
        all_vertices.append(tile_vertices)
        all_faces.append(tile_mesh.faces + face_offset)

        # Update face offset for the next tile
        face_offset += len(tile_vertices)

    # Combine all tiles into a single UV fabric
    uv_fabric = trimesh.Trimesh(
        vertices=np.vstack(all_vertices), faces=np.vstack(all_faces)
    )

    return uv_fabric


if __name__ == "__main__":
    json_file_path = Path("data/planet.json")
    output_uv_path = Path("debug/output_uv_fabric.stl")
    output_sphere_path = Path("debug/output_sphere.stl")
    radius = 10
    smoothing_iterations = 1

    create_uv_mapped_sphere(
        json_file_path, output_uv_path, output_sphere_path, radius, smoothing_iterations
    )
