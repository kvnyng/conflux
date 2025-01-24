import cv2
import mediapipe as mp
from pathlib import Path


# Function to capitalize first letter of name and convert to CamelCase
def to_camel_case_with_capital(name: str) -> str:
    words = name.split()
    return "".join(word.capitalize() for word in words)


def extract_palm_region(
    image_path: Path,
    output_normal_path: Path,
    output_greyscale_path: Path,
    size: int,
    threshold: float = 0.7,
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

    # Convert the image to RGB for Mediapipe
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
    result = hands.process(image_rgb)

    if not result.multi_hand_landmarks:
        raise ValueError(
            "No hand detected in the image. Please upload a better quality image of your hand."
        )

    # Perform a weighted average of the landmarks to find the center of the hand

    LANDMARKS_OF_INTEREST = {
        mp_hands.HandLandmark.WRIST: 1,
        mp_hands.HandLandmark.THUMB_MCP: 1,
        mp_hands.HandLandmark.INDEX_FINGER_MCP: 1,
        mp_hands.HandLandmark.MIDDLE_FINGER_MCP: 1,
        mp_hands.HandLandmark.PINKY_MCP: 1,
    }
    # print(result.multi_hand_landmarks)

    for hand_landmarks in result.multi_hand_landmarks:
        h, w, _ = image.shape
        # print(hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x)
        # Calculate the geometric center of all landmarks
        center_x = int(
            sum(
                hand_landmarks.landmark[landmark].x * w * weight
                for landmark, weight in LANDMARKS_OF_INTEREST.items()
            )
            / sum(weight for weight in LANDMARKS_OF_INTEREST.values())
        )

        center_y = int(
            sum(
                hand_landmarks.landmark[landmark].y * h * weight
                for landmark, weight in LANDMARKS_OF_INTEREST.items()
            )
            / sum(weight for weight in LANDMARKS_OF_INTEREST.values())
        )

        # Find the bounding box based on the landmarks of interest
        x_min = min(
            int(hand_landmarks.landmark[landmark].x * w)
            for landmark in LANDMARKS_OF_INTEREST.keys()
        )
        x_max = max(
            int(hand_landmarks.landmark[landmark].x * w)
            for landmark in LANDMARKS_OF_INTEREST.keys()
        )
        y_min = min(
            int(hand_landmarks.landmark[landmark].y * h)
            for landmark in LANDMARKS_OF_INTEREST.keys()
        )
        y_max = max(
            int(hand_landmarks.landmark[landmark].y * h)
            for landmark in LANDMARKS_OF_INTEREST.keys()
        )

    # print(f"Center: ({center_x}, {center_y})")
    # print(f"Bounding Box: ({x_min}, {y_min}) to ({x_max}, {y_max})")

    landmarks_of_interest_width = int(x_max - x_min)
    landmarks_of_interest_height = int(y_max - y_min)

    crop_scale = 0.75

    # # Take the min size of the bounding box
    crop_size = int(
        crop_scale * min(landmarks_of_interest_width, landmarks_of_interest_height)
    )
    # print(f"Crop Size: {crop_size}")

    # Crop a square region around the center
    # crop_size = 800  # Define the size of the square
    x_start = max(0, center_x - crop_size // 2)
    y_start = max(0, center_y - crop_size // 2)
    x_end = min(w, center_x + crop_size // 2)
    y_end = min(h, center_y + crop_size // 2)

    cropped_palm = image[y_start:y_end, x_start:x_end]

    # Resize the cropped palm image
    cropped_palm = cv2.resize(cropped_palm, (size, size))

    # Save the cropped palm image in greyscale
    cv2.imwrite(str(output_normal_path), cropped_palm, [cv2.IMWRITE_PNG_COMPRESSION, 9])

    # greyscale version of the cropped palm
    greyscale_palm = cv2.cvtColor(cropped_palm, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(
        str(output_greyscale_path),
        greyscale_palm,
        [
            cv2.IMWRITE_PNG_COMPRESSION,
            9,
        ],
    )

    # Clean up the Mediapipe Hands object
    hands.close()


if __name__ == "__main__":
    image_path = Path(
        "server/uploads/images/raw/IdaChen_a5a853539942fd681ed835dfc305b4b8.jpeg"
    )
    output_path = Path("server/uploads/images/palms/debug.png")
    extract_palm_region(image_path, output_path)
    print(f"Extracted palm region saved to {output_path}")
