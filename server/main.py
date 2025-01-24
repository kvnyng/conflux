from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import hashlib
from datetime import datetime

from scripts.palm import extract_palm_region, to_camel_case_with_capital
from scripts.landscape import generate_3d_mesh_from_heightmap

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
PLANET_FILE = Path("data") / "planet.json"

LANDSCAPES_FOLDER = "data/landscapes"

PLANET_FOLDER = "data/planets"

INDEX_PAGE_FILE = Path("docs") / "index.html"
SCAN_PAGE_FILE = Path("docs") / "scan.html"


Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PALM_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PALM_NORMAL_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PALM_GREYSCALE_FOLDER).mkdir(parents=True, exist_ok=True)
Path(LANDSCAPES_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PLANET_FOLDER).mkdir(parents=True, exist_ok=True)


# Initialize the JSON data file if it doesn't exist
if not DATA_FILE.exists():
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

if not PLANET_FILE.exists():
    with open(PLANET_FILE, "w") as f:
        json.dump({}, f)

if not INDEX_PAGE_FILE.exists():
    raise FileNotFoundError(f"File not found: {INDEX_PAGE_FILE}")

if not SCAN_PAGE_FILE.exists():
    raise FileNotFoundError(f"File not found: {SCAN_PAGE_FILE}")


@app.get("/")
async def root():
    return FileResponse(INDEX_PAGE_FILE)


@app.get("/scan/")
async def scan():
    return FileResponse(SCAN_PAGE_FILE)


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

        with open(PLANET_FILE, "r") as f:
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

        try:
            generate_3d_mesh_from_heightmap(
                palm_greyscale_file_location,
                landscapes_file_location,
                sigma=5,
                margin=20,
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
                "message": "File uploaded and processed successfully!",
                "data": new_entry,
            },
            status_code=200,
        )

    except Exception as e:
        print(f"An error occurred: {str(e)}")  # Log error details
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/favicon.ico")
async def favicon():
    return RedirectResponse(url="/assets/favicon/favicon.ico")


# Serve static files (e.g., uploaded images)
app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/client", StaticFiles(directory="docs"), name="docs")
