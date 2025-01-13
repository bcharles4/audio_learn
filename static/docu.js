document.addEventListener("DOMContentLoaded", () => {
    const readBtn = document.getElementById("read-btn");
    const pauseBtn = document.getElementById("pause-btn");
    const stopBtn = document.getElementById("stop-btn");
    const voiceCommandBtn = document.getElementById("voiceCommand-btn");
    const bookmarkBtn = document.getElementById("bookmark-btn");

    const bookmarkContainer = document.getElementById("bookmark-container");
    const bookmarkedItems = document.getElementById("bookmarked-items");
    const closeBookmarkContainer = document.getElementById("close-bookmark-container");

    // Text-to-Speech Setup
    const speechSynthesis = window.speechSynthesis;
    let currentUtterance = null;
    let isPaused = false;
    let isVoiceCommandActive = false;

    const resetSpeech = () => {
        if (speechSynthesis.speaking || speechSynthesis.pending) {
            speechSynthesis.cancel();
        }
    };

    const startSpeechRecognition = (recognition) => {
        try {
            recognition.start();
            console.log("Voice recognition started.");
        } catch (error) {
            console.error("Error starting voice recognition:", error);
        }
    };

    const stopSpeechRecognition = (recognition) => {
        try {
            recognition.stop();
            console.log("Voice recognition stopped.");
        } catch (error) {
            console.error("Error stopping voice recognition:", error);
        }
    };

    // Speech Recognition Setup
    let recognition = null;
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = "en-US";
        recognition.continuous = true; // Allow continuous listening
        recognition.interimResults = false;

        recognition.onresult = (event) => {
            let spokenCommand = event.results[event.results.length - 1][0].transcript.trim().toLowerCase();
            spokenCommand = spokenCommand.replace(/[.,!?]$/, ""); // Remove trailing punctuation
            console.log(`Command recognized: "${spokenCommand}"`);
        
            const acknowledgeCommand = (responseText, callback) => {
                // Stop reading immediately for priority commands
                if (speechSynthesis.speaking || speechSynthesis.paused) {
                    speechSynthesis.cancel();
                }
        
                // Acknowledge the command using TTS
                const acknowledgment = new SpeechSynthesisUtterance(responseText);
                acknowledgment.onend = () => {
                    // Perform the actual action after acknowledgment finishes
                    if (callback) callback();
                };
                speechSynthesis.speak(acknowledgment);
            };
        
            if (["read", "read aloud", "start reading"].includes(spokenCommand)) {
                acknowledgeCommand("Alright master, I'll read aloud", () => {
                    readBtn?.click();
                });
            } else if (["pause", "hold"].includes(spokenCommand)) {
                if (speechSynthesis.speaking && !speechSynthesis.paused) {
                    acknowledgeCommand("Pausing the reading now.", () => {
                        speechSynthesis.pause();
                    });
                } else {
                    acknowledgeCommand("Reading is already paused.");
                }
            } else if (["resume", "continue"].includes(spokenCommand)) {
                if (speechSynthesis.paused) {
                    acknowledgeCommand("Resuming the reading.", () => {
                        speechSynthesis.resume();
                    });
                } else {
                    acknowledgeCommand("Reading is already ongoing.");
                }
            } else if (["stop", "cancel", "end"].includes(spokenCommand)) {
                acknowledgeCommand("Stopping the reading.", () => {
                    resetSpeech(); // Stop the speech synthesis
                });
            } else {
                console.log(`Command not recognized: "${spokenCommand}"`);
                acknowledgeCommand(`Command "${spokenCommand}" not recognized. Please try again.`);
            }
        };
        
            

        recognition.onerror = (event) => {
            console.error("Speech recognition error:", event.error);
        };

        recognition.onend = () => {
            console.log("Voice recognition ended.");
            if (isVoiceCommandActive) {
                startSpeechRecognition(recognition); // Restart for continuous listening
            }
        };
    } else {
        alert("Voice recognition is not supported in this browser.");
    }

    readBtn?.addEventListener("click", () => {
        const visibleParagraph = document.querySelector(".paragraph-container");
        if (visibleParagraph) {
            const textToRead = visibleParagraph.innerText.trim();
            if (textToRead) {
                resetSpeech();
    
                // Split the paragraph into words and wrap each word in a span
                const words = textToRead.split(/\s+/);
                visibleParagraph.innerHTML = words
                    .map((word) => `<span class="word">${word}</span>`)
                    .join(" ");
    
                const wordElements = visibleParagraph.querySelectorAll(".word");
    
                currentUtterance = new SpeechSynthesisUtterance(textToRead);
    
                let wordIndex = 0;
    
                // Highlight the currently spoken word
                currentUtterance.onboundary = (event) => {
                    if (event.name === "word") {
                        // Remove highlight from all words
                        wordElements.forEach((word) => word.classList.remove("highlight"));
    
                        // Highlight the current word
                        if (wordElements[wordIndex]) {
                            wordElements[wordIndex].classList.add("highlight");
                        }
                        wordIndex++;
                    }
                };
    
                currentUtterance.onend = () => {
                    console.log("Reading completed.");
                    // Remove highlight after reading
                    wordElements.forEach((word) => word.classList.remove("highlight"));
                };
    
                speechSynthesis.speak(currentUtterance);
            } else {
                alert("No text available to read.");
            }
        } else {
            alert("No paragraph available to read.");
        }
    });
    
    pauseBtn?.addEventListener("click", () => {
        const icon = pauseBtn.querySelector("ion-icon");
        if (speechSynthesis.speaking) {
            if (speechSynthesis.paused) {
                speechSynthesis.resume();
                icon?.setAttribute("name", "pause-outline");
                isPaused = false;
            } else {
                speechSynthesis.pause();
                icon?.setAttribute("name", "caret-forward-outline");
                isPaused = true;
            }
        } else {
            alert("No speech to pause or resume.");
        }
    });

    stopBtn?.addEventListener("click", () => {
        if (speechSynthesis.speaking || isPaused) {
            resetSpeech();
            isPaused = false;
            const icon = pauseBtn.querySelector("ion-icon");
            icon?.setAttribute("name", "pause-outline");
        } else {
            alert("No speech to stop.");
        }
    });

    voiceCommandBtn?.addEventListener("click", () => {
        const icon = voiceCommandBtn.querySelector("ion-icon");

        if (!isVoiceCommandActive) {
            isVoiceCommandActive = true;
            icon?.setAttribute("name", "mic-off-outline");
            if (recognition) startSpeechRecognition(recognition);
        } else {
            isVoiceCommandActive = false;
            icon?.setAttribute("name", "mic-outline");
            if (recognition) stopSpeechRecognition(recognition);
        }
    });

    bookmarkBtn?.addEventListener("click", () => {
        const visibleParagraph = document.querySelector(".paragraph-container");
        if (visibleParagraph) {
            const paragraphText = visibleParagraph.innerText.trim();

            const existingBookmarks = Array.from(bookmarkedItems.children).map(
                (item) => item.innerText
            );
            if (existingBookmarks.includes(paragraphText)) {
                alert("This paragraph is already bookmarked.");
                return;
            }

            const newBookmark = document.createElement("li");
            newBookmark.innerText = paragraphText;
            bookmarkedItems.appendChild(newBookmark);
            bookmarkContainer.style.display = "block";
        } else {
            alert("No paragraph available to bookmark.");
        }
    });

    closeBookmarkContainer?.addEventListener("click", () => {
        bookmarkContainer.style.display = "none";
    });
});


document.getElementById('delete-btn').addEventListener('click', function() {
    // Get user information from localStorage
    const user = JSON.parse(localStorage.getItem("user"));
    const { firstname, lastname, usersID } = user;

    const filename = this.getAttribute('data-filename'); // Retrieve the filename stored in the button data attribute

    // Confirm the action with the user
    const isConfirmed = confirm("Are you sure you want to delete this module?");

    if (isConfirmed) {
        // Send the filename to the backend using fetch
        fetch('/delete_file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filename: filename }) // Send the filename to delete
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert('File deleted successfully');
                // Reload the page to reflect changes
                window.location.href = '/book/' + usersID;  // Redirect to the book page
            } else {

                window.location.href = '/book/' + usersID;  // Reload to show updated data
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the file.');
        });
    } else {
        // If the user cancels, simply exit without doing anything
        console.log("File deletion cancelled.");
    }
});

