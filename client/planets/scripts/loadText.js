// Function to fetch text from a file and update an element
async function loadText(filePath, elementId) {
    try {
        const response = await fetch(filePath); // Fetch the text file
        if (!response.ok) {
            throw new Error(`Failed to load ${filePath}: ${response.statusText}`);
        }
        const text = await response.text(); // Parse the response as text

        // Split text into lines and wrap each line in a <div> or add <br>
        const formattedText = text
            .split('\n') // Split text into lines
            .map(line => line.trim() === '' ? '<br>' : `<div>${line}</div>`) // Handle empty lines with <br>
            .join(''); // Join all lines into a single string

        document.getElementById(elementId).innerHTML = formattedText; // Update the element's content with HTML
    } catch (error) {
        console.error(`Error loading text file: ${error}`);
    }
}

// Load left and right text files
loadText('./assets/left-text.txt', 'left-text'); // Load left text
loadText('./assets/right-text.txt', 'right-text'); // Load right text