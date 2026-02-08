// ========================================
// Configuration & Constants
// ========================================

const CONFIG = {
    ENDPOINT: "/chat",
    HEALTH_ENDPOINT: "/health",
    AGENTS_ENDPOINT: "/agents",
    HEALTH_CHECK_INTERVAL: 5000,
    MAX_CONVERSATION_LENGTH: 10
};

// ========================================
// State Management
// ========================================

const state = {
    agents: [],
    conversation: [],
    currentMention: "",
    selectedSuggestionIndex: -1
};

// ========================================
// DOM References
// ========================================

const elements = {
    chatArea: null,
    questionInput: null,
    sendBtn: null,
    statusIndicator: null,
    agentSuggestions: null,
    teamList: null
};

// ========================================
// Initialization
// ========================================

function initializeApp() {
    // Cache DOM elements
    elements.chatArea = document.getElementById("chatArea");
    elements.questionInput = document.getElementById("questionInput");
    elements.sendBtn = document.getElementById("sendBtn");
    elements.statusIndicator = document.getElementById("statusIndicator");
    elements.agentSuggestions = document.getElementById("agentSuggestions");
    elements.teamList = document.getElementById("teamList");
    
    // Setup event listeners
    setupEventListeners();
    
    // Load initial data
    loadAgents();
    checkConnection();
    
    // Focus input
    elements.questionInput.focus();
}

function setupEventListeners() {
    // Input events
    elements.questionInput.addEventListener("input", handleInputChange);
    elements.questionInput.addEventListener("keydown", handleKeyDown);
    
    // Send button
    elements.sendBtn.addEventListener("click", sendQuestion);
    
    // Close suggestions when clicking outside
    document.addEventListener("click", (e) => {
        if (e.target !== elements.questionInput && e.target !== elements.agentSuggestions) {
            closeSuggestions();
        }
    });
}

// ========================================
// Agent Management
// ========================================

async function loadAgents() {
    try {
        const response = await fetch(CONFIG.AGENTS_ENDPOINT);
        if (response.ok) {
            const data = await response.json();
            state.agents = data.agents || [];
            renderTeamList();
            console.log("[+] Loaded agents:", state.agents);
        } else {
            console.error("[!] Failed to load agents");
            state.agents = [];
        }
    } catch (error) {
        console.error("[!] Error loading agents:", error);
        state.agents = [];
    }
}

function renderTeamList() {
    if (state.agents.length === 0) {
        elements.teamList.innerHTML = '<p style="color: #94a3b8; padding: 16px;">Loading team...</p>';
        return;
    }
    
    elements.teamList.innerHTML = state.agents.map(agent => `
        <div class="agent-item" data-key="${agent.key}" data-name="${agent.name}" data-avatar="${agent.avatar}">
            <img class="agent-item-avatar" src="${agent.avatar}" alt="${agent.name}" />
            <div class="agent-item-info">
                <span class="agent-item-name">${agent.name}</span>
                <span class="agent-item-role">${agent.role} (AI Agent)</span>
            </div>
        </div>
    `).join("");
    
    // Add click handlers
    elements.teamList.querySelectorAll(".agent-item").forEach(item => {
        item.addEventListener("click", () => {
            selectAgent(item.dataset.key, item.dataset.name, item.dataset.avatar);
        });
    });
}

// ========================================
// Connection Status
// ========================================

async function checkConnection() {
    try {
        const response = await fetch(CONFIG.HEALTH_ENDPOINT, { method: "GET" });
        updateStatus(response.ok);
    } catch (error) {
        updateStatus(false);
    }
    
    setTimeout(checkConnection, CONFIG.HEALTH_CHECK_INTERVAL);
}

function updateStatus(connected) {
    if (connected) {
        elements.statusIndicator.innerHTML = `
            <div class="status-badge connected">
                <span class="status-dot connected"></span>
                <span>Connected</span>
            </div>
        `;
        elements.sendBtn.disabled = false;
    } else {
        elements.statusIndicator.innerHTML = `
            <div class="status-badge disconnected">
                <span class="status-dot disconnected"></span>
                <span>Disconnected</span>
            </div>
        `;
        elements.sendBtn.disabled = true;
    }
}

// ========================================
// @Mention Autocomplete
// ========================================

function handleInputChange(e) {
    const text = e.target.value;
    const cursorPos = e.target.selectionStart;
    
    // Find if we're in an @ mention
    const atIndex = text.lastIndexOf("@", cursorPos - 1);
    if (atIndex === -1) {
        closeSuggestions();
        return;
    }
    
    // Check if there's a space or special char after @
    const afterAt = text.substring(atIndex + 1, cursorPos);
    if (afterAt.includes(" ") || afterAt.includes("\n")) {
        closeSuggestions();
        return;
    }
    
    state.currentMention = afterAt.toLowerCase();
    
    // Show matching suggestions
    const filtered = state.agents.filter(agent => 
        agent.name.toLowerCase().includes(state.currentMention) ||
        agent.key.toLowerCase().includes(state.currentMention)
    );
    
    if (filtered.length > 0) {
        showSuggestions(filtered);
    } else {
        closeSuggestions();
    }
}

function showSuggestions(agents) {
    const html = agents.map((agent, index) => `
        <div class="agent-suggestion-item" 
             data-index="${index}" 
             data-key="${agent.key}" 
             data-name="${agent.name}" 
             data-avatar="${agent.avatar}">
            <img class="agent-suggestion-avatar" src="${agent.avatar}" alt="${agent.name}" />
            <div class="agent-suggestion-info">
                <strong>${agent.name}</strong>
                <small>${agent.role}</small>
            </div>
        </div>
    `).join("");
    
    elements.agentSuggestions.innerHTML = html;
    elements.agentSuggestions.classList.add("active");
    state.selectedSuggestionIndex = -1;
    
    // Add click handlers
    elements.agentSuggestions.querySelectorAll(".agent-suggestion-item").forEach(item => {
        item.addEventListener("click", () => {
            selectAgent(item.dataset.key, item.dataset.name, item.dataset.avatar);
        });
    });
}

function closeSuggestions() {
    elements.agentSuggestions.classList.remove("active");
    state.currentMention = "";
    state.selectedSuggestionIndex = -1;
}

function updateSuggestionSelection() {
    const items = elements.agentSuggestions.querySelectorAll(".agent-suggestion-item");
    items.forEach((item, idx) => {
        if (idx === state.selectedSuggestionIndex) {
            item.classList.add("selected");
            item.scrollIntoView({ block: "nearest", behavior: "smooth" });
        } else {
            item.classList.remove("selected");
        }
    });
}

function selectHighlightedSuggestion() {
    if (state.selectedSuggestionIndex === -1) return false;
    
    const items = elements.agentSuggestions.querySelectorAll(".agent-suggestion-item");
    const selectedItem = items[state.selectedSuggestionIndex];
    if (!selectedItem) return false;
    
    selectAgent(
        selectedItem.dataset.key,
        selectedItem.dataset.name,
        selectedItem.dataset.avatar
    );
    return true;
}

function selectAgent(key, name, avatar) {
    const isAutocomplete = elements.agentSuggestions.classList.contains("active");
    let text = elements.questionInput.value;
    
    if (isAutocomplete) {
        // Replace @mention with @name (autocomplete scenario)
        const atIndex = text.lastIndexOf("@");
        if (atIndex !== -1) {
            const beforeAt = text.substring(0, atIndex);
            const afterCursor = text.substring(elements.questionInput.selectionStart);
            text = beforeAt + "@" + name + " " + afterCursor;
            elements.questionInput.value = text;
            const newPos = beforeAt.length + name.length + 2;
            elements.questionInput.setSelectionRange(newPos, newPos);
        }
    } else {
        // Just append @name to input (clicked from sidebar)
        const currentValue = elements.questionInput.value;
        const needsSpace = currentValue && !currentValue.endsWith(" ");
        elements.questionInput.value = currentValue + (needsSpace ? " " : "") + "@" + name + " ";
        elements.questionInput.setSelectionRange(elements.questionInput.value.length, elements.questionInput.value.length);
    }
    
    closeSuggestions();
    elements.questionInput.focus();
}

// ========================================
// Keyboard Navigation
// ========================================

function handleKeyDown(e) {
    const isSuggestionsActive = elements.agentSuggestions.classList.contains("active");
    
    if (isSuggestionsActive) {
        const items = elements.agentSuggestions.querySelectorAll(".agent-suggestion-item");
        const maxIndex = items.length - 1;
        
        if (e.key === "ArrowDown") {
            e.preventDefault();
            state.selectedSuggestionIndex = Math.min(state.selectedSuggestionIndex + 1, maxIndex);
            updateSuggestionSelection();
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            state.selectedSuggestionIndex = Math.max(state.selectedSuggestionIndex - 1, -1);
            updateSuggestionSelection();
        } else if (e.key === "Enter") {
            if (state.selectedSuggestionIndex !== -1) {
                e.preventDefault();
                selectHighlightedSuggestion();
            }
        } else if (e.key === "Escape") {
            e.preventDefault();
            closeSuggestions();
        }
    } else if (e.key === "Enter") {
        e.preventDefault();
        sendQuestion();
    }
}

// ========================================
// Chat & Messaging
// ========================================

async function sendQuestion() {
    const question = elements.questionInput.value.trim();
    if (!question) return;
    
    // Add user message to chat
    addMessage(question, "user");
    state.conversation.push({ role: "user", text: question });
    
    // Trim conversation history
    if (state.conversation.length > CONFIG.MAX_CONVERSATION_LENGTH) {
        state.conversation.splice(0, state.conversation.length - CONFIG.MAX_CONVERSATION_LENGTH);
    }
    
    elements.questionInput.value = "";
    elements.questionInput.focus();
    
    // Show loading
    const loadingEl = addLoadingMessage();
    elements.sendBtn.disabled = true;
    
    try {
        const payload = { messages: state.conversation };
        
        console.log("Sending request to", CONFIG.ENDPOINT, "with payload:", payload);
        
        const response = await fetch(CONFIG.ENDPOINT, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(payload),
            mode: "cors"
        });
        
        console.log("Response status:", response.status);
        
        const bodyText = await response.text();
        console.log("Response body:", bodyText);
        
        if (response.ok) {
            let result;
            try {
                result = bodyText ? JSON.parse(bodyText) : {};
            } catch {
                result = { output: bodyText };
            }
            
            removeMessage(loadingEl);
            
            // Handle both single and multiple responses
            if (Array.isArray(result.responses)) {
                result.responses.forEach(resp => displayResponse(resp));
            } else {
                displayResponse(result);
            }
        } else {
            removeMessage(loadingEl);
            
            let errorText;
            try {
                const errorData = JSON.parse(bodyText);
                errorText = errorData.detail || errorData.message || JSON.stringify(errorData);
            } catch {
                errorText = bodyText || response.statusText;
            }
            addMessage(`Error: ${response.status} - ${errorText || 'Unknown error'}`, "assistant");
        }
    } catch (error) {
        removeMessage(loadingEl);
        console.error("Fetch error:", error);
        addMessage(`Error: ${error.message}. Make sure the business team is running (python run.py)`, "assistant");
    } finally {
        elements.sendBtn.disabled = false;
        elements.questionInput.focus();
    }
}

function displayResponse(result) {
    let responseText = "";
    let agentName = "";
    
    // Extract response text
    if (typeof result === "string") {
        responseText = result;
    } else if (result.output) {
        responseText = result.output;
    } else if (result.response) {
        responseText = result.response;
    } else if (result.messages && Array.isArray(result.messages)) {
        responseText = result.messages
            .map(msg => {
                if (typeof msg === "string") return msg;
                return msg.content || msg.text || msg.output || JSON.stringify(msg);
            })
            .join("\n\n");
    } else if (Object.keys(result).length > 0) {
        responseText = JSON.stringify(result, null, 2);
    } else {
        responseText = "No response received";
    }
    
    // Build agent header if available
    let headerHtml = "";
    if (result && typeof result === "object") {
        agentName = result.agent_meta && result.agent_meta.name
            ? String(result.agent_meta.name)
            : (result.agent ? String(result.agent) : "");
        const avatarUrl = result.agent_avatar
            ? String(result.agent_avatar)
            : (result.agent_meta && result.agent_meta.avatar_url ? String(result.agent_meta.avatar_url) : "");
        
        if (agentName) {
            const avatarHtml = avatarUrl
                ? `<img class="agent-avatar" src="${avatarUrl}" alt="${agentName}" />`
                : "";
            headerHtml = `<div class="agent-header">${avatarHtml}<span>${agentName}</span></div>`;
        }
    }
    
    const safeText = escapeHtml(responseText).replace(/\n/g, "<br />");
    addMessage(headerHtml + safeText, "assistant", true);
    
    // Add to conversation history
    if (responseText) {
        const agentPrefix = agentName ? `(${agentName}) ` : "";
        state.conversation.push({ role: "assistant", text: `${agentPrefix}${responseText}` });
        if (state.conversation.length > CONFIG.MAX_CONVERSATION_LENGTH) {
            state.conversation.splice(0, state.conversation.length - CONFIG.MAX_CONVERSATION_LENGTH);
        }
    }
}

function addMessage(content, role, useHtml = false) {
    const messageEl = document.createElement("div");
    messageEl.className = `message ${role}`;
    
    const contentEl = document.createElement("div");
    contentEl.className = "message-content";
    
    const bubbleEl = document.createElement("div");
    bubbleEl.className = "message-bubble";
    
    if (useHtml) {
        bubbleEl.innerHTML = content;
    } else {
        bubbleEl.textContent = content;
    }
    
    contentEl.appendChild(bubbleEl);
    messageEl.appendChild(contentEl);
    elements.chatArea.appendChild(messageEl);
    
    // Scroll to bottom
    elements.chatArea.scrollTop = elements.chatArea.scrollHeight;
    
    return messageEl;
}

function addLoadingMessage() {
    const messageEl = document.createElement("div");
    messageEl.className = "message assistant";
    
    const contentEl = document.createElement("div");
    contentEl.className = "message-content";
    
    const bubbleEl = document.createElement("div");
    bubbleEl.className = "message-bubble";
    
    const spinner = document.createElement("div");
    spinner.className = "loading";
    spinner.innerHTML = "<span></span><span></span><span></span>";
    
    bubbleEl.appendChild(spinner);
    contentEl.appendChild(bubbleEl);
    messageEl.appendChild(contentEl);
    elements.chatArea.appendChild(messageEl);
    
    elements.chatArea.scrollTop = elements.chatArea.scrollHeight;
    
    return messageEl;
}

function removeMessage(messageEl) {
    messageEl.remove();
}

// ========================================
// Utilities
// ========================================

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ========================================
// App Entry Point
// ========================================

// Initialize when DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeApp);
} else {
    initializeApp();
}
