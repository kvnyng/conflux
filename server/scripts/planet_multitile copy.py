import numpy as np
import trimesh
import os


def map_to_sphere(vertices, theta_bounds, phi_bounds, R):
    """
    Maps a flat tile's vertices onto a spherical tile.
    """
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]
    phi = phi_bounds[0] + x * (phi_bounds[1] - phi_bounds[0])
    theta = theta_bounds[0] + y * (theta_bounds[1] - theta_bounds[0])
    new_x = (R + z) * np.sin(theta) * np.cos(phi)
    new_y = (R + z) * np.sin(theta) * np.sin(phi)
    new_z = (R + z) * np.cos(theta)
    return np.column_stack((new_x, new_y, new_z))


def create_tiled_sphere_from_folder(input_folder, output_stl_path, R=1, N=5):
    """
    Creates a tiled sphere using multiple STL files from a folder.
    """
    stl_files = [
        os.path.join(input_folder, f)
        for f in os.listdir(input_folder)
        if f.endswith(".stl")
    ]
    if len(stl_files) < N:
        print(
            f"Warning: Only found {len(stl_files)} STL files, expected {N}. Some areas will be left blank, which is normal behavior."
        )

    tile_meshes = [trimesh.load(stl_files[i]) for i in range(len(stl_files))]

    M = int(np.sqrt(N))  # Latitude bands
    N_per_band = int(N / M)  # Tiles per band
    theta_edges = np.linspace(0, np.pi, M + 1)
    phi_edges = np.linspace(0, 2 * np.pi, N_per_band + 1)

    all_vertices = []
    all_faces = []
    face_offset = 0

    tile_idx = 0
    for lat_idx in range(len(theta_edges) - 1):
        for lon_idx in range(len(phi_edges) - 1):
            if tile_idx >= len(tile_meshes):
                continue  # Proceed with blank areas as normal behavior

            tile_mesh = tile_meshes[tile_idx]
            theta_bounds = (theta_edges[lat_idx], theta_edges[lat_idx + 1])
            phi_bounds = (phi_edges[lon_idx], phi_edges[lon_idx + 1])

            mapped_vertices = map_to_sphere(
                tile_mesh.vertices, theta_bounds, phi_bounds, R
            )
            all_vertices.append(mapped_vertices)
            all_faces.append(tile_mesh.faces + face_offset)
            face_offset += len(mapped_vertices)
            tile_idx += 1

    # Ensure an STL file is exported even if some tiles are missing
    all_vertices = np.vstack(all_vertices) if all_vertices else np.empty((0, 3))
    all_faces = np.vstack(all_faces) if all_faces else np.empty((0, 3), dtype=int)

    tiled_sphere_mesh = trimesh.Trimesh(vertices=all_vertices, faces=all_faces)
    tiled_sphere_mesh.export(output_stl_path)
    print(
        f"Tiled sphere saved to {output_stl_path}, even if some areas are left blank."
    )


if __name__ == "__main__":
    input_folder = "./data/landscapes"
    output_stl_path = "./data/planet/planet.stl"
    create_tiled_sphere_from_folder(input_folder, output_stl_path, R=1, N=50)
