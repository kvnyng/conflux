import cv2
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import os
import hashlib
from datetime import datetime
import mediapipe as mp
import random

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
UPLOAD_FOLDER = "uploads/images/raw"
SEGMENTED_FOLDER = "uploads/segmented"
PALM_FOLDER = "uploads/palms"
DATA_FILE = Path("uploads") / "data.json"
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(SEGMENTED_FOLDER).mkdir(parents=True, exist_ok=True)
Path(PALM_FOLDER).mkdir(parents=True, exist_ok=True)

# Initialize the JSON data file if it doesn't exist
if not DATA_FILE.exists():
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)


# Function to capitalize first letter of name and convert to CamelCase
def to_camel_case_with_capital(name: str) -> str:
    words = name.split()
    return "".join(word.capitalize() for word in words)


# Function to process the segmented image to find the most interesting square
async def process_palm_image(segmented_image_path: Path, output_path: Path):
    # Load the segmented image
    image = cv2.imread(str(segmented_image_path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Could not read the segmented image file.")

    # Convert the image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)

    # Find contours in the grayscale image
    contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create a metric to identify the most interesting square
    def calculate_interest_metric(square):
        return cv2.Laplacian(
            square, cv2.CV_64F
        ).var()  # Variance of Laplacian measures texture/liveliness

    # Iterate over random square regions to find the most interesting one
    h, w = gray.shape
    square_size = min(h, w) // 4  # Size of the square regions
    max_metric = 0
    best_square = None

    for _ in range(20):  # Test 20 random square regions
        x = random.randint(0, w - square_size)
        y = random.randint(0, h - square_size)
        square = gray[y : y + square_size, x : x + square_size]

        metric = calculate_interest_metric(square)
        if metric > max_metric:
            max_metric = metric
            best_square = (x, y, square_size)

    if best_square is None:
        raise ValueError("Could not find an interesting square region.")

    # Extract the most interesting square and save it
    x, y, size = best_square
    interesting_square = image[y : y + size, x : x + size]
    cv2.imwrite(str(output_path), interesting_square, [cv2.IMWRITE_PNG_COMPRESSION, 9])


# Function to process and detect hand, segment, and mask out non-hand areas using detailed landmarks
def process_hand_image_with_mediapipe(
    image_path: Path, output_path: Path, threshold: float = 0.7
):
    # Load the image
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError("Could not read the image file.")

    # Initialize Mediapipe Hands
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    hands = mp_hands.Hands(
        static_image_mode=True, max_num_hands=1, min_detection_confidence=threshold
    )

    # Convert the image to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    result = hands.process(image_rgb)

    if not result.multi_hand_landmarks:
        raise ValueError(
            "No hand detected in the image. Please upload a better quality image of your hand."
        )

    # Create a mask for the hand using detailed landmarks
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    for hand_landmarks in result.multi_hand_landmarks:
        h, w, _ = image.shape
        landmark_points = [
            (int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark
        ]

        # Use the landmarks to create a detailed hand contour
        hull = cv2.convexHull(np.array(landmark_points))
        cv2.fillConvexPoly(mask, hull, 255)

        # Draw additional segments using the connections between landmarks
        connections = mp_hands.HAND_CONNECTIONS
        for connection in connections:
            pt1 = landmark_points[connection[0]]
            pt2 = landmark_points[connection[1]]
            cv2.line(mask, pt1, pt2, 255, thickness=2)

    # Apply the mask to the original image
    segmented_image = cv2.bitwise_and(image, image, mask=mask)

    # Convert black background to transparent
    bgr = cv2.split(segmented_image)
    alpha_channel = mask
    rgba = cv2.merge((*bgr, alpha_channel))

    # Save the segmented image as a PNG
    cv2.imwrite(str(output_path), rgba, [cv2.IMWRITE_PNG_COMPRESSION, 9])


@app.post("/upload/")
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

        # Process the image for hand detection and segmentation
        segmented_file_location = Path(SEGMENTED_FOLDER) / hashed_filename.replace(
            Path(file.filename).suffix, ".png"
        )
        palm_file_location = Path(PALM_FOLDER) / hashed_filename.replace(
            Path(file.filename).suffix, "_palm.png"
        )
        try:
            process_hand_image_with_mediapipe(file_location, segmented_file_location)
            await process_palm_image(segmented_file_location, palm_file_location)
        except ValueError as e:
            # Delete the raw file if processing fails
            if file_location.exists():
                file_location.unlink()
            raise HTTPException(status_code=400, detail=str(e))

        # Add or overwrite the client's entry
        timestamp = datetime.utcnow().isoformat()  # Convert datetime to string
        new_entry = {
            "name": name,
            "photo": str(file_location),
            "segmented_photo": str(segmented_file_location),
            "palm_photo": str(palm_file_location),
            "timestamp": timestamp,  # Already a string
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


# Serve static files (e.g., uploaded images)
app.mount("/static", StaticFiles(directory="uploads"), name="static")
