/**
 * Napa Valley AI Concierge - Pro Widget
 * Multi-tenant embeddable chat widget with analytics & lead capture
 *
 * Usage: <script src="https://your-domain.com/widget.js" data-api-key="nc_xxx"></script>
 */

(function() {
    'use strict';

    // Get API key from script tag
    const scriptTag = document.currentScript || document.querySelector('script[data-api-key]');
    const API_KEY = scriptTag?.getAttribute('data-api-key') || window.NAPA_CONCIERGE_KEY;

    if (!API_KEY) {
        console.error('Napa Concierge: Missing API key. Add data-api-key="your_key" to the script tag.');
        return;
    }

    // Configuration - can be overridden by server config
    let CONFIG = {
        apiUrl: scriptTag?.getAttribute('data-api-url') || window.NAPA_CONCIERGE_API || 'http://localhost:8000',
        primaryColor: '#722F37',
        businessName: 'Concierge',
        widgetTitle: 'Concierge',
        widgetSubtitle: 'Your personal wine country guide',
        welcomeMessage: "Hello! I'm your Napa Valley concierge. How can I help you today?"
    };

    let conversationHistory = [];
    let sessionId = null;
    let isLoading = false;
    let configLoaded = false;
    let proactiveShown = false;

    // Generate or retrieve session ID
    function getSessionId() {
        if (sessionId) return sessionId;
        sessionId = sessionStorage.getItem('nc_session') || 'nc_' + Math.random().toString(36).substr(2, 16);
        sessionStorage.setItem('nc_session', sessionId);
        return sessionId;
    }

    // Load configuration from server
    async function loadConfig() {
        try {
            const response = await fetch(`${CONFIG.apiUrl}/widget/config?api_key=${API_KEY}`);
            if (response.ok) {
                const config = await response.json();
                CONFIG.businessName = config.business_name || CONFIG.businessName;
                CONFIG.primaryColor = config.primary_color || CONFIG.primaryColor;
                CONFIG.widgetTitle = config.widget_title || CONFIG.widgetTitle;
                CONFIG.widgetSubtitle = config.widget_subtitle || CONFIG.widgetSubtitle;
                CONFIG.welcomeMessage = config.welcome_message || CONFIG.welcomeMessage;
                configLoaded = true;
                applyBranding();
            }
        } catch (error) {
            console.warn('Napa Concierge: Could not load config, using defaults');
        }
    }

    // Apply custom branding colors
    function applyBranding() {
        const widget = document.getElementById('napa-concierge-widget');
        if (widget) {
            widget.style.setProperty('--nc-primary', CONFIG.primaryColor);
            widget.style.setProperty('--nc-primary-dark', adjustColor(CONFIG.primaryColor, -20));
        }

        const headerText = document.getElementById('napa-concierge-header-text');
        if (headerText) {
            headerText.querySelector('h3').textContent = CONFIG.widgetTitle;
            headerText.querySelector('p').textContent = CONFIG.widgetSubtitle;
        }
    }

    // Darken/lighten a hex color
    function adjustColor(hex, percent) {
        const num = parseInt(hex.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return '#' + (0x1000000 +
            (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)
        ).toString(16).slice(1);
    }

    // Create widget HTML
    function createWidget() {
        const container = document.createElement('div');
        container.id = 'napa-concierge-widget';
        container.innerHTML = `
            <div id="napa-concierge-proactive" style="display: none;">
                <span id="napa-concierge-proactive-close">&times;</span>
                <p>Planning a visit? I can help with reservations and recommendations!</p>
            </div>

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
                        <h3>${CONFIG.widgetTitle}</h3>
                        <p>${CONFIG.widgetSubtitle}</p>
                    </div>
                    <button id="napa-concierge-close" aria-label="Close chat">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                        </svg>
                    </button>
                </div>

                <div id="napa-concierge-messages"></div>

                <!-- Lead capture form (hidden by default) -->
                <div id="napa-concierge-lead-form" style="display: none;">
                    <div class="nc-lead-content">
                        <p>Want us to follow up with you?</p>
                        <input type="text" id="nc-lead-name" placeholder="Your name" />
                        <input type="email" id="nc-lead-email" placeholder="Email address" />
                        <input type="tel" id="nc-lead-phone" placeholder="Phone (optional)" />
                        <div class="nc-lead-buttons">
                            <button id="nc-lead-submit">Submit</button>
                            <button id="nc-lead-cancel">No thanks</button>
                        </div>
                    </div>
                </div>

                <div id="napa-concierge-input-area">
                    <input type="text" id="napa-concierge-input" placeholder="Ask about wineries, restaurants, activities..." />
                    <button id="napa-concierge-send" aria-label="Send message">
                        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                        </svg>
                    </button>
                </div>

                <div id="napa-concierge-footer">
                    Powered by <a href="#" target="_blank">Napa Concierge AI</a>
                </div>
            </div>
        `;

        document.body.appendChild(container);
    }

    // Load CSS (inject inline to avoid external file dependency)
    function loadStyles() {
        const existingStyle = document.getElementById('napa-concierge-styles');
        if (existingStyle) return;

        const style = document.createElement('style');
        style.id = 'napa-concierge-styles';
        style.textContent = `
            #napa-concierge-widget {
                --nc-primary: ${CONFIG.primaryColor};
                --nc-primary-dark: ${adjustColor(CONFIG.primaryColor, -20)};
                --nc-secondary: #8B7355;
                --nc-light: #F5F0EB;
                --nc-white: #FFFFFF;
                --nc-text: #333333;
                --nc-text-light: #666666;
                --nc-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                font-size: 14px;
                line-height: 1.5;
            }
            #napa-concierge-toggle {
                position: fixed;
                bottom: 24px;
                right: 24px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, var(--nc-primary) 0%, var(--nc-primary-dark) 100%);
                border: none;
                cursor: pointer;
                box-shadow: var(--nc-shadow);
                display: flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                z-index: 9998;
            }
            #napa-concierge-toggle:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 32px rgba(0, 0, 0, 0.2);
            }
            #napa-concierge-toggle svg {
                width: 28px;
                height: 28px;
                fill: var(--nc-white);
            }
            #napa-concierge-chat {
                position: fixed;
                bottom: 100px;
                right: 24px;
                width: 380px;
                max-width: calc(100vw - 48px);
                height: 520px;
                max-height: calc(100vh - 140px);
                background: var(--nc-white);
                border-radius: 16px;
                box-shadow: var(--nc-shadow);
                display: none;
                flex-direction: column;
                overflow: hidden;
                z-index: 9999;
                animation: ncSlideUp 0.3s ease;
            }
            #napa-concierge-chat.open { display: flex; }
            @keyframes ncSlideUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            #napa-concierge-header {
                background: linear-gradient(135deg, var(--nc-primary) 0%, var(--nc-primary-dark) 100%);
                color: var(--nc-white);
                padding: 16px 20px;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            #napa-concierge-header-icon {
                width: 40px;
                height: 40px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            #napa-concierge-header-icon svg {
                width: 24px;
                height: 24px;
                fill: var(--nc-white);
            }
            #napa-concierge-header-text h3 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            #napa-concierge-header-text p {
                margin: 2px 0 0 0;
                font-size: 12px;
                opacity: 0.9;
            }
            #napa-concierge-close {
                margin-left: auto;
                background: none;
                border: none;
                color: var(--nc-white);
                cursor: pointer;
                padding: 4px;
                opacity: 0.8;
                transition: opacity 0.2s;
            }
            #napa-concierge-close:hover { opacity: 1; }
            #napa-concierge-messages {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
                background: var(--nc-light);
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            .nc-message {
                max-width: 85%;
                padding: 12px 16px;
                border-radius: 16px;
                word-wrap: break-word;
            }
            .nc-message.assistant {
                background: var(--nc-white);
                color: var(--nc-text);
                align-self: flex-start;
                border-bottom-left-radius: 4px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
            }
            .nc-message.user {
                background: var(--nc-primary);
                color: var(--nc-white);
                align-self: flex-end;
                border-bottom-right-radius: 4px;
            }
            .nc-message.assistant a {
                color: var(--nc-primary);
                text-decoration: underline;
            }
            .nc-message.assistant strong { color: var(--nc-primary); }
            .nc-typing {
                display: flex;
                gap: 4px;
                padding: 12px 16px;
                background: var(--nc-white);
                border-radius: 16px;
                border-bottom-left-radius: 4px;
                align-self: flex-start;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
            }
            .nc-typing span {
                width: 8px;
                height: 8px;
                background: var(--nc-secondary);
                border-radius: 50%;
                animation: ncBounce 1.4s infinite ease-in-out;
            }
            .nc-typing span:nth-child(1) { animation-delay: -0.32s; }
            .nc-typing span:nth-child(2) { animation-delay: -0.16s; }
            @keyframes ncBounce {
                0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
                40% { transform: scale(1); opacity: 1; }
            }
            #napa-concierge-input-area {
                padding: 12px 16px;
                background: var(--nc-white);
                border-top: 1px solid #eee;
                display: flex;
                gap: 8px;
            }
            #napa-concierge-input {
                flex: 1;
                padding: 10px 14px;
                border: 1px solid #ddd;
                border-radius: 24px;
                outline: none;
                font-size: 14px;
                transition: border-color 0.2s;
            }
            #napa-concierge-input:focus { border-color: var(--nc-primary); }
            #napa-concierge-send {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: var(--nc-primary);
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            }
            #napa-concierge-send:hover { background: var(--nc-primary-dark); }
            #napa-concierge-send:disabled { background: #ccc; cursor: not-allowed; }
            #napa-concierge-send svg { width: 18px; height: 18px; fill: var(--nc-white); }
            #napa-concierge-footer {
                padding: 8px;
                text-align: center;
                font-size: 11px;
                color: var(--nc-text-light);
                background: var(--nc-white);
                border-top: 1px solid #eee;
            }
            #napa-concierge-footer a { color: var(--nc-primary); text-decoration: none; }

            /* Lead capture form */
            #napa-concierge-lead-form {
                position: absolute;
                bottom: 60px;
                left: 0;
                right: 0;
                background: var(--nc-white);
                padding: 16px;
                border-top: 1px solid #eee;
                box-shadow: 0 -4px 12px rgba(0,0,0,0.1);
            }
            .nc-lead-content p { margin: 0 0 12px 0; font-weight: 500; }
            .nc-lead-content input {
                width: 100%;
                padding: 8px 12px;
                margin-bottom: 8px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
            }
            .nc-lead-buttons { display: flex; gap: 8px; margin-top: 8px; }
            .nc-lead-buttons button {
                flex: 1;
                padding: 10px;
                border-radius: 8px;
                border: none;
                cursor: pointer;
                font-size: 14px;
            }
            #nc-lead-submit { background: var(--nc-primary); color: white; }
            #nc-lead-cancel { background: #eee; color: #666; }

            /* Proactive popup */
            #napa-concierge-proactive {
                position: fixed;
                bottom: 94px;
                right: 24px;
                background: var(--nc-white);
                padding: 16px 20px;
                border-radius: 12px;
                box-shadow: var(--nc-shadow);
                max-width: 260px;
                z-index: 9997;
                animation: ncFadeIn 0.4s ease;
            }
            #napa-concierge-proactive p {
                margin: 0;
                font-size: 14px;
                color: var(--nc-text);
                line-height: 1.5;
            }
            #napa-concierge-proactive-close {
                position: absolute;
                top: 8px;
                right: 12px;
                font-size: 18px;
                color: #999;
                cursor: pointer;
                line-height: 1;
            }
            #napa-concierge-proactive-close:hover { color: #666; }
            #napa-concierge-proactive::after {
                content: '';
                position: absolute;
                bottom: -8px;
                right: 28px;
                width: 0;
                height: 0;
                border-left: 8px solid transparent;
                border-right: 8px solid transparent;
                border-top: 8px solid var(--nc-white);
            }
            @keyframes ncFadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @media (max-width: 480px) {
                #napa-concierge-chat {
                    bottom: 0;
                    right: 0;
                    width: 100%;
                    max-width: 100%;
                    height: 100%;
                    max-height: 100%;
                    border-radius: 0;
                }
                #napa-concierge-toggle { bottom: 16px; right: 16px; }
                #napa-concierge-proactive { right: 16px; bottom: 86px; }
            }
        `;
        document.head.appendChild(style);
    }

    // Add message to chat
    function addMessage(content, role) {
        const messagesContainer = document.getElementById('napa-concierge-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `nc-message ${role}`;

        if (role === 'assistant') {
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
            .replace(/^### (.+)$/gm, '<strong>$1</strong>')
            .replace(/^## (.+)$/gm, '<br><strong style="font-size: 1.05em;">$1</strong><br>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/^- (.+)$/gm, '&bull; $1<br>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>')
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
                    'X-API-Key': API_KEY
                },
                body: JSON.stringify({
                    message: message,
                    conversation_history: conversationHistory,
                    session_id: getSessionId()
                })
            });

            if (!response.ok) {
                throw new Error('Failed to get response');
            }

            const data = await response.json();

            hideTyping();
            addMessage(data.response, 'assistant');
            conversationHistory = data.conversation_history;
            sessionId = data.session_id;

            // Check if AI mentioned contact/follow-up to show lead form
            if (data.response.toLowerCase().includes('follow up') ||
                data.response.toLowerCase().includes('contact info') ||
                data.response.toLowerCase().includes('reach out')) {
                setTimeout(showLeadForm, 1000);
            }

        } catch (error) {
            console.error('Napa Concierge Error:', error);
            hideTyping();
            addMessage("I apologize, but I'm having trouble connecting right now. Please try again in a moment.", 'assistant');
        } finally {
            isLoading = false;
            sendButton.disabled = false;
            input.focus();
        }
    }

    // Lead capture functions
    function showLeadForm() {
        document.getElementById('napa-concierge-lead-form').style.display = 'block';
    }

    function hideLeadForm() {
        document.getElementById('napa-concierge-lead-form').style.display = 'none';
    }

    async function submitLead() {
        const name = document.getElementById('nc-lead-name').value;
        const email = document.getElementById('nc-lead-email').value;
        const phone = document.getElementById('nc-lead-phone').value;

        if (!email && !phone) {
            alert('Please enter at least an email or phone number.');
            return;
        }

        try {
            await fetch(`${CONFIG.apiUrl}/lead`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': API_KEY
                },
                body: JSON.stringify({
                    session_id: getSessionId(),
                    name: name,
                    email: email,
                    phone: phone,
                    interest: 'Chat inquiry'
                })
            });

            hideLeadForm();
            addMessage("Thanks! Someone from our team will be in touch soon.", 'assistant');
        } catch (error) {
            console.error('Lead capture error:', error);
            alert('Sorry, there was an error. Please try again.');
        }
    }

    // Initialize widget
    async function init() {
        loadStyles();
        createWidget();
        await loadConfig();
        applyBranding();

        const toggle = document.getElementById('napa-concierge-toggle');
        const chat = document.getElementById('napa-concierge-chat');
        const close = document.getElementById('napa-concierge-close');
        const input = document.getElementById('napa-concierge-input');
        const send = document.getElementById('napa-concierge-send');

        // Toggle chat
        toggle.addEventListener('click', function() {
            chat.classList.add('open');
            toggle.style.display = 'none';

            // Hide proactive popup if visible
            const proactive = document.getElementById('napa-concierge-proactive');
            if (proactive) proactive.style.display = 'none';

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

        // Lead form handlers
        document.getElementById('nc-lead-submit').addEventListener('click', submitLead);
        document.getElementById('nc-lead-cancel').addEventListener('click', hideLeadForm);

        // Proactive popup - show after 10 seconds if chat not opened
        const proactive = document.getElementById('napa-concierge-proactive');
        const proactiveClose = document.getElementById('napa-concierge-proactive-close');

        setTimeout(function() {
            if (!proactiveShown && !chat.classList.contains('open')) {
                proactive.style.display = 'block';
                proactiveShown = true;
            }
        }, 10000);

        // Close proactive popup
        proactiveClose.addEventListener('click', function(e) {
            e.stopPropagation();
            proactive.style.display = 'none';
        });

        // Click proactive popup to open chat
        proactive.addEventListener('click', function() {
            proactive.style.display = 'none';
            toggle.click();
        });
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
