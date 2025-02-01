from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request, logger
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import hashlib
from datetime import datetime
import os

from scripts.palm import extract_palm_region, to_camel_case_with_capital
from scripts.landscape import generate_3d_mesh_from_heightmap
from scripts.planet_one_palm import create_tiled_sphere
from scripts.planet_multitile import create_tiled_sphere_from_folder

from starlette.responses import FileResponse


app = FastAPI()

# Enable CORS for testing purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to store uploaded photos and data file
UPLOAD_FOLDER = "data/images/raw"
PALM_FOLDER = "data/images/palms"
PALM_NORMAL_FOLDER = PALM_FOLDER + "/normal"
PALM_GREYSCALE_FOLDER = PALM_FOLDER + "/greyscale"
DATA_FILE = Path("data") / "scheme.json"
PLANETS_FILE = Path("data") / "planet.json"

LANDSCAPES_FOLDER = "data/landscapes"

PLANETS_FOLDER = "data/planets"
PLANET_FOLDER = "data/planet"

# INDEX_PAGE_FILE = Path("index.html")
# INDEX_PAGE_FILE = Path("docs") / "index.html"


Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PALM_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PALM_NORMAL_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PALM_GREYSCALE_FOLDER).mkdir(parents=True, exist_ok=True)
Path(LANDSCAPES_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PLANETS_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PLANET_FOLDER).mkdir(parents=True, exist_ok=True)

# Initialize the JSON data file if it doesn't exist
if not DATA_FILE.exists():
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

if not PLANETS_FILE.exists():
    with open(PLANETS_FILE, "w") as f:
        json.dump({}, f)

# if not INDEX_PAGE_FILE.exists():
#     raise FileNotFoundError(f"File not found: {INDEX_PAGE_FILE}")


@app.api_route("/", methods=["GET", "POST", "HEAD"])
async def root():
    return {"message": "Welcome to the Palm to Planet API!"}


# @app.get("/scan/")
# async def scan():
#     return FileResponse(SCAN_PAGE_FILE)


@app.post("/scan/upload/")
async def upload_file(
    request: Request, name: str = Form(...), file: UploadFile = File(...)
):
    try:
        client_ip = request.client.host
        file_content = await file.read()
        file_hash = hashlib.md5(file_content).hexdigest()

        # Capitalize first letter and convert to CamelCase
        capitalized_name = to_camel_case_with_capital(name)
        hashed_filename = f"{capitalized_name}_{file_hash}{Path(file.filename).suffix}"

        # Load existing data
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("data.json is not a dictionary!")

        with open(PLANETS_FILE, "r") as f:
            planet_data = json.load(f)
            if not isinstance(planet_data, dict):
                raise ValueError("planet.json is not a dictionary!")

        # Check if client IP already exists and delete the old file if necessary
        if client_ip in data:
            old_file_path = data[client_ip]["photo"]
            old_file = Path(old_file_path)
            if old_file.exists():
                old_file.unlink()  # Delete the old file

        # Save the new file
        file_location = Path(UPLOAD_FOLDER) / hashed_filename
        with open(file_location, "wb") as buffer:
            buffer.write(file_content)

        palm_normal_file_location = Path(PALM_NORMAL_FOLDER) / hashed_filename.replace(
            Path(file.filename).suffix, "_palm_normal.png"
        )
        palm_greyscale_file_location = Path(
            PALM_GREYSCALE_FOLDER
        ) / hashed_filename.replace(Path(file.filename).suffix, "_palm_greyscale.png")

        try:
            extract_palm_region(
                file_location,
                palm_normal_file_location,
                palm_greyscale_file_location,
                640,
            )
        except ValueError as e:
            # Delete the raw file if processing fails
            if file_location.exists():
                file_location.unlink()
            raise HTTPException(status_code=400, detail=str(e))

        landscapes_file_location = Path(LANDSCAPES_FOLDER) / hashed_filename.replace(
            Path(file.filename).suffix, "_landscapes.stl"
        )

        planets_file_location = Path(PLANETS_FOLDER) / hashed_filename.replace(
            Path(file.filename).suffix, "_planet.stl"
        )

        planet_file_location = Path(PLANET_FOLDER) / hashed_filename.replace(
            Path(file.filename).suffix, "_planet.stl"
        )

        try:
            generate_3d_mesh_from_heightmap(
                palm_greyscale_file_location,
                landscapes_file_location,
                sigma=5,
                margin=20,
            )
            create_tiled_sphere(
                landscapes_file_location, planets_file_location, R=1, N=50
            )
            create_tiled_sphere_from_folder(
                LANDSCAPES_FOLDER, planet_file_location, R=1, N=50
            )

        except Exception as e:
            # Delete the raw file if processing fails
            if file_location.exists():
                file_location.unlink()
            if palm_normal_file_location.exists():
                palm_normal_file_location.unlink()
            if palm_greyscale_file_location.exists():
                palm_greyscale_file_location.unlink()
            raise HTTPException(status_code=400, detail=str(e))

        # Add or overwrite the client's entry
        timestamp = datetime.utcnow().isoformat()  # Convert datetime to string
        new_entry = {
            "name": name,
            "photo": str(file_location),
            "palm_normal_photo": str(palm_normal_file_location),
            "palm_greyscale_photo": str(palm_greyscale_file_location),
            "timestamp": timestamp,  # Already a string
            "landscapes": str(landscapes_file_location),
        }
        data[client_ip] = new_entry

        # Save updated data
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        return JSONResponse(
            content={
                "UUID": client_ip,
                "message": "File uploaded and processed successfully!",
                "data": new_entry,
            },
            status_code=200,
        )

    except Exception as e:
        print(f"An error occurred: {str(e)}")  # Log error details
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("landscape/stl/{client_ip}")
async def get_client_stl(client_ip: str):
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("data.json is not a dictionary!")

        if client_ip not in data:
            raise HTTPException(status_code=404, detail="Client not found.")

        client_data = data[client_ip]
        landscapes_file_location = Path(client_data["landscapes"])

        if not landscapes_file_location.exists():
            raise HTTPException(status_code=404, detail="3D landscape file not found.")

        return FileResponse(
            landscapes_file_location,
            media_type="application/vnd.ms-pkistl",
            filename=landscapes_file_location.name,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/planets/stl/latest")
async def get_latest_stl():
    try:
        # Get all .stl files in the LANDSCAPES_FOLDER
        stl_files = list(Path(PLANETS_FOLDER).glob("*.stl"))

        if not stl_files:
            raise HTTPException(status_code=404, detail="No STL files found.")

        # Find the latest .stl file based on modification time
        latest_stl = max(stl_files, key=os.path.getmtime)

        return FileResponse(
            latest_stl, media_type="application/vnd.ms-pkistl", filename=latest_stl.name
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/planet/latest")
async def get_latest_planet():
    try:
        stl_files = list(Path(PLANET_FOLDER).glob("*.stl"))

        if not stl_files:
            raise HTTPException(status_code=404, detail="No STL files found.")

        latest_stl = max(stl_files, key=os.path.getmtime)

        return FileResponse(
            latest_stl, media_type="application/vnd.ms-pkistl", filename=latest_stl.name
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/palm/latest")
async def get_latest_palm():
    try:
        # Get all .images files in the PALM_GREYSCALE_FOLDER
        grey_images = list(Path(PALM_GREYSCALE_FOLDER).glob("*.png"))

        if not grey_images:
            raise HTTPException(status_code=404, detail="No images files found.")

        # Find the latest .stl file based on modification time
        latest_image = max(grey_images, key=os.path.getmtime)

        return FileResponse(
            latest_image, media_type="image/png", filename=latest_image.name
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/planet/stl/latest")
async def get_latest_stl():
    try:
        # Get all .stl files in the LANDSCAPES_FOLDER
        stl_files = list(Path(PLANETS_FOLDER).glob("*.stl"))

        if not stl_files:
            raise HTTPException(status_code=404, detail="No STL files found.")

        # Find the latest .stl file based on modification time
        latest_stl = max(stl_files, key=os.path.getmtime)

        return FileResponse(
            latest_stl, media_type="application/vnd.ms-pkistl", filename=latest_stl.name
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/landscape/latest")
async def get_latest_planet():
    try:
        # Get all .json files in the PLANET_FOLDER
        landscapes = list(Path(LANDSCAPES_FOLDER).glob("*.stl"))

        # Find the latest .json file based on modification time
        latest_landscape = max(landscapes, key=os.path.getmtime)

        return FileResponse(
            latest_landscape,
            media_type="application/json",
            filename=latest_landscape.name,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@app.get("/favicon.ico")
async def favicon():
    return RedirectResponse(url="/assets/favicon/favicon.ico")


# Serve static files (e.g., uploaded images)
app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
# app.mount("/docs", StaticFiles(directory="docs"), name="docs")
