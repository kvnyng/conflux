const SERVER_URL = "http://api.cosmicimprint.org"
const ENDPOINT_STL = SERVER_URL + "/planet/stl/latest";

fetch(ENDPOINT_PALM_IMAGE)
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.blob(); // Get the image as a Blob
    })
    .then(blob => {
        const imageUrl = URL.createObjectURL(blob); // Convert Blob to an Object URL
        const image = document.getElementById("handPrint");
        image.src = imageUrl; // Set the image source
        console.log("Got the image");
    })
    .catch(error => {
        console.error("Error fetching the image:", error);
    });
