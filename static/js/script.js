
const promptInput = document.getElementById("prompt");
const sendButton = document.getElementById("sendButton");
const projectFolder = document.getElementById("projectFolder");
const input = document.getElementById("input");

let projectUploaded = false;
let onetime = false;
async function sendPrompt() {

    const prompt = promptInput.value.trim();

    if (!prompt) {
        return;
    }

   
    const formData = new FormData();
    formData.append("prompt", prompt);


    if(projectFolder.files.length > 0 && !projectUploaded){
        formData.append("new_project", "true")
        for(const file of projectFolder.files){
            formData.append("files", file, file.webkitRelativePath);
        }
        projectUploaded = true;
        onetime = true;
    }

    appendMessage("User", prompt)
    scrollToBottom();
    promptInput.value = "";
    input.innerText = "";
    // Disable button while agent is working
    sendButton.disabled = true;
    sendButton.textContent = "Run Agent ➤";

    showTyping()
   
    try {
       
        const response = await fetch("/chat", {
            method: "POST",

            // headers: {
            //     "Content-Type": "application/json"
            // },

            body: formData
        });
        if (!response.ok) {
            throw new Error("Server error: " + response.status);
        }

        const data = await response.json();
        document.getElementById("typing")?.remove();
        appendMessage("Agent", data.response);
        if (data.project_modified) {
            showDownloadButton();
        }
        scrollToBottom();

    } catch (error) {

        console.error("Error:", error);
        document.getElementById("typing")?.remove();
        appendMessage("Agent", "Something went wrong while contacting the agent.")

    } finally {

        sendButton.disabled = false;
        sendButton.textContent = "Run Agent ➤";
    }
}

function appendMessage(sender, text) {
    let welcome = document.getElementById("welcome");
    let chatBox = document.getElementById("chat-box");

    welcome.style.display = "none";
    let msg = document.createElement("div");

    msg.classList.add("message");

    if (sender === "User") {
        msg.classList.add("user");
        if (onetime) {
            msg.innerHTML = `${text}
            <br>Attached Folder: 📁 ${selectedFolderName}`;
            onetime = false;
        }
        else{
            msg.innerHTML = `${text}`;
        }
    } else{
        msg.classList.add("agent");
        msg.innerHTML = DOMPurify.sanitize(marked.parse(String(text)));
        // msg.innerHTML = `${text}`;
        styleDiffBlocks(msg)
    }
    // msg.innerHTML = `${text}`;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function showTyping() {
    let chatBox = document.getElementById("chat-box");
    let typing = document.createElement("div");
    typing.id = "typing";
    typing.innerHTML = `
        <div class="typing-bubble">
            <span></span><span></span><span></span>
        </div>
    `;
    chatBox.appendChild(typing);
}

// Button click
sendButton.addEventListener("click", async() => {
    sendPrompt()
});

let selectedFiles = [];
let selectedFolderName = "";

projectFolder.addEventListener('change', (event) =>{
    const files = event.target.files;
    if(files.length === 0) return;
    projectUploaded = false;
    selectedFiles = Array.from(files);

    const firstFilePath = selectedFiles[0].webkitRelativePath;
    selectedFolderName = firstFilePath.split('/')[0];

    input.innerText = `Attached Folder: 📁 ${selectedFolderName}`;
});

// Enter = send
promptInput.addEventListener("keydown", function(event) {

    if (event.key === "Enter" && !event.shiftKey) {

        event.preventDefault();

        sendPrompt();
    }

});

function scrollToBottom(){
    const chat = document.querySelector(".chat")
    chat.scrollTo({
        top: chat.scrollHeight,
        behavior: "smooth"
    });
}

function styleDiffBlocks(container) {
    const diffBlocks = container.querySelectorAll("pre code.language-diff");
    diffBlocks.forEach(codeBlock => {
        const lines = codeBlock.textContent.split("\n");
        codeBlock.innerHTML = "";
        lines.forEach(line => {
            const lineDiv = document.createElement("div");
            lineDiv.classList.add("diff-line");
            if (line.startsWith("+")){
                lineDiv.classList.add("diff-added");
            }else if (line.startsWith("-")){
                lineDiv.classList.add("diff-removed");
            }else if (line.startsWith("@@")){
                lineDiv.classList.add("diff-info");
            }
            lineDiv.textContent = line;
            codeBlock.appendChild(lineDiv);
        });
    });
}

function showDownloadButton() {
    const button = document.getElementById("download-project-btn");
    button.style.display = "block";
}

function downloadProject() {
    window.location.href = "/download-project";
}