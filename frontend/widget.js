/**
 * Napa Valley AI Concierge - Embeddable Chat Widget
 * Drop this script on any hotel website to add AI concierge functionality
 */

(function() {
    'use strict';

    // Configuration - hotels can customize these
    const CONFIG = {
        apiUrl: window.NAPA_CONCIERGE_API || 'http://localhost:8000',
        hotelName: window.NAPA_CONCIERGE_HOTEL || 'your hotel',
        primaryColor: window.NAPA_CONCIERGE_COLOR || '#722F37',
        welcomeMessage: window.NAPA_CONCIERGE_WELCOME || "Hello! I'm your Napa Valley concierge. I can help you plan wine tastings, find amazing restaurants, and discover local experiences. What brings you to wine country?"
    };

    let conversationHistory = [];
    let isLoading = false;

    // Create widget HTML
    function createWidget() {
        const container = document.createElement('div');
        container.id = 'napa-concierge-widget';
        container.innerHTML = `
            <button id="napa-concierge-toggle" aria-label="Open chat">
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.36 5.07L2 22l4.93-1.36C8.42 21.5 10.15 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm-1 15h-2v-2h2v2zm2.07-7.75l-.9.92C11.45 10.9 11 11.5 11 13h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H6c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/>
                </svg>
            </button>

            <div id="napa-concierge-chat">
                <div id="napa-concierge-header">
                    <div id="napa-concierge-header-icon">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.36 5.07L2 22l4.93-1.36C8.42 21.5 10.15 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2z"/>
                        </svg>
                    </div>
                    <div id="napa-concierge-header-text">
                        <h3>Napa Valley Concierge</h3>
                        <p>Your personal wine country guide</p>
                    </div>
                    <button id="napa-concierge-close" aria-label="Close chat">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                </div>

                <div id="napa-concierge-messages"></div>

                <div id="napa-concierge-input-area">
                    <input type="text" id="napa-concierge-input" placeholder="Ask about wineries, restaurants, activities..." />
                    <button id="napa-concierge-send" aria-label="Send message">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>

                <div id="napa-concierge-footer">
                    Powered by <a href="#">Napa Concierge AI</a>
                </div>
            </div>
        `;

        document.body.appendChild(container);
    }

    // Load CSS
    function loadStyles() {
        // Check if running locally or from CDN
        const existingStyle = document.querySelector('link[href*="widget.css"]');
        if (!existingStyle) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = CONFIG.apiUrl.replace('/api', '') + '/widget.css';

            // Fallback: inject inline styles if external CSS fails
            link.onerror = function() {
                console.log('Loading inline styles for Napa Concierge widget');
            };

            document.head.appendChild(link);
        }
    }

    // Add message to chat
    function addMessage(content, role) {
        const messagesContainer = document.getElementById('napa-concierge-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `nc-message ${role}`;

        if (role === 'assistant') {
            // Parse markdown-like formatting
            messageDiv.innerHTML = formatMessage(content);
        } else {
            messageDiv.textContent = content;
        }

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Markdown formatter for chat messages
    function formatMessage(text) {
        return text
            // Headers - convert to bold with line break
            .replace(/^### (.+)$/gm, '<strong>$1</strong>')
            .replace(/^## (.+)$/gm, '<br><strong style="color: var(--nc-primary, #722F37); font-size: 1.05em;">$1</strong><br>')
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // List items - convert to bullet points
            .replace(/^- (.+)$/gm, '&bull; $1<br>')
            // Line breaks
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>')
            // Clean up multiple breaks
            .replace(/(<br>){3,}/g, '<br><br>');
    }

    // Show typing indicator
    function showTyping() {
        const messagesContainer = document.getElementById('napa-concierge-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'nc-typing';
        typingDiv.id = 'nc-typing-indicator';
        typingDiv.innerHTML = '<span></span><span></span><span></span>';
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Hide typing indicator
    function hideTyping() {
        const typing = document.getElementById('nc-typing-indicator');
        if (typing) typing.remove();
    }

    // Send message to API
    async function sendMessage(message) {
        if (isLoading || !message.trim()) return;

        isLoading = true;
        const sendButton = document.getElementById('napa-concierge-send');
        const input = document.getElementById('napa-concierge-input');

        sendButton.disabled = true;
        input.value = '';

        addMessage(message, 'user');
        showTyping();

        try {
            const response = await fetch(`${CONFIG.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_history: conversationHistory
                })
            });

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            const data = await response.json();

            hideTyping();
            addMessage(data.response, 'assistant');
            conversationHistory = data.conversation_history;

        } catch (error) {
            console.error('Napa Concierge Error:', error);
            hideTyping();
            addMessage("I apologize, but I'm having trouble connecting right now. Please try again in a moment, or contact the front desk for immediate assistance.", 'assistant');
        } finally {
            isLoading = false;
            sendButton.disabled = false;
            input.focus();
        }
    }

    // Initialize widget
    function init() {
        createWidget();
        loadStyles();

        const toggle = document.getElementById('napa-concierge-toggle');
        const chat = document.getElementById('napa-concierge-chat');
        const close = document.getElementById('napa-concierge-close');
        const input = document.getElementById('napa-concierge-input');
        const send = document.getElementById('napa-concierge-send');

        // Toggle chat
        toggle.addEventListener('click', function() {
            chat.classList.add('open');
            toggle.style.display = 'none';

            // Show welcome message if first open
            if (conversationHistory.length === 0) {
                addMessage(CONFIG.welcomeMessage, 'assistant');
            }

            input.focus();
        });

        // Close chat
        close.addEventListener('click', function() {
            chat.classList.remove('open');
            toggle.style.display = 'flex';
        });

        // Send on button click
        send.addEventListener('click', function() {
            sendMessage(input.value);
        });

        // Send on Enter
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage(input.value);
            }
        });
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
