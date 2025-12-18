const chatHistory = document.getElementById('chat-history');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const fileInput = document.getElementById('file-upload');
const uploadStatus = document.getElementById('upload-status');

// Handle File Upload
fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    uploadStatus.textContent = "Uploading & Processing...";

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            uploadStatus.textContent = "Done! " + file.name;
            addMessage(`System: Uploaded ${file.name} (${data.extracted_chars} chars extracted).`, 'bot-message');
        } else {
            uploadStatus.textContent = "Error uploading.";
            console.error(data);
        }
    } catch (error) {
        uploadStatus.textContent = "Network Error.";
        console.error(error);
    }
});

// Handle Chat
async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;

    addMessage(text, 'user-message');
    userInput.value = '';

    // Show loading state
    const loadingId = addMessage("Thinking...", 'bot-message');

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();

        // Remove loading message
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();

        if (response.ok) {
            console.log("Chat Response Data:", data);
            addMessage(data.response, 'bot-message', data.time_taken);
        } else {
            addMessage("Error: Could not get response.", 'bot-message');
        }
    } catch (error) {
        console.error(error);
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) loadingMsg.remove();
        addMessage("Error: Network issue.", 'bot-message');
    }
}

function addMessage(text, className, duration = null) {
    const div = document.createElement('div');
    div.className = `message ${className}`;

    const contentDiv = document.createElement('div');

    // Parse Markdown for bot messages
    if (className.includes('bot-message')) {
        contentDiv.innerHTML = marked.parse(text);
    } else {
        contentDiv.textContent = text;
    }

    div.appendChild(contentDiv);

    if (duration !== null && typeof duration === 'number') {
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = `Generated in ${duration.toFixed(2)}s`;
        div.appendChild(timeDiv);
    }

    div.id = 'msg-' + Date.now();
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return div.id;
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
