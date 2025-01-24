// script.js

const SERVER_URL = "http://10.250.144.197:8000"
const ENDPOINT_AUDIO = SERVER_URL + "/planet/audio/";

let audioPlayer;

const audio_path = "./assets/narration.mp3"

// Function to initialize the audio player
function initializeAudio() {
    // Create an audio element
    audioPlayer = document.createElement("audio");
    audioPlayer.autoplay = true;
    audioPlayer.controls = true; // Optional if you want browser-native controls
    document.body.appendChild(audioPlayer);

    // Fetch the latest audio file and set it as the source
    fetch(AUDIO_API_ENDPOINT)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to fetch audio file: ${response.statusText}`);
            }
            return response.blob();
        })
        .then(blob => {
            const audioURL = URL.createObjectURL(blob);
            audioPlayer.src = audio_path;
            // audioPlayer.src = audioURL;
        })
        .catch(error => {
            console.error("Error loading audio file:", error);
            alert("Failed to load audio. Please try again later.");
        });
}

// Function to toggle play/pause
function togglePlayPause() {
    const playPauseButton = document.getElementById("audio-button-play");
    if (audioPlayer.paused) {
        audioPlayer.play();
        playPauseButton.textContent = "Pause";
    } else {
        audioPlayer.pause();
        playPauseButton.textContent = "Play";
    }
}

// Function to toggle mute
function toggleMute() {
    const muteButton = document.getElementById("audio-button-mute");
    audioPlayer.muted = !audioPlayer.muted;
    muteButton.textContent = audioPlayer.muted ? "Unmute" : "Mute";
}

// Add event listeners for buttons
window.onload = () => {
    initializeAudio();

    const playPauseButton = document.getElementById("audio-button-play");
    const muteButton = document.getElementById("audio-button-mute");

    playPauseButton.addEventListener("click", togglePlayPause);
    muteButton.addEventListener("click", toggleMute);
};