/**
 * FITORA AI Assistant Floating Chat Widget
 * Handles conversational queries, FAQ retrieval, nutrition balance, error codes,
 * support ticket creation, and MongoDB feedback submission.
 */

document.addEventListener('DOMContentLoaded', () => {
    const trigger = document.getElementById('fitoraAiTrigger');
    const chatWindow = document.getElementById('fitoraChatWindow');
    const closeBtn = document.getElementById('chatCloseBtn');
    const sendBtn = document.getElementById('chatSendBtn');
    const input = document.getElementById('chatInput');
    const messagesContainer = document.getElementById('chatMessages');

    if (!trigger || !chatWindow) return;

    // Retrieve or initialize unique conversation ID
    let conversationId = sessionStorage.getItem('fitora_conv_id');
    if (!conversationId) {
        conversationId = 'conv_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
        sessionStorage.setItem('fitora_conv_id', conversationId);
    }

    // Toggle Chat Window
    trigger.addEventListener('click', (e) => {
        e.preventDefault();
        const isHidden = chatWindow.style.display === 'none' || chatWindow.classList.contains('d-none');
        if (isHidden) {
            chatWindow.style.display = 'flex';
            chatWindow.classList.remove('d-none');
            input.focus();
            scrollToBottom();
        } else {
            chatWindow.style.display = 'none';
        }
    });

    closeBtn.addEventListener('click', () => {
        chatWindow.style.display = 'none';
    });

    // Send Message
    function sendMessage(textToSend) {
        const text = textToSend || input.value.trim();
        if (!text) return;

        // Render User Message
        appendMessage('user', text);
        input.value = '';

        // Show typing indicator
        const typingId = showTypingIndicator();

        // Get CSRF Token
        const csrfToken = getCsrfToken();

        fetch('/assistant/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                message: text,
                conversation_id: conversationId,
                page: window.location.pathname
            })
        })
        .then(response => {
            removeTypingIndicator(typingId);
            if (!response.ok) {
                throw new Error(`Server returned HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            appendMessage('ai', data.response, data);
        })
        .catch(err => {
            removeTypingIndicator(typingId);
            appendMessage('ai', "I'm having trouble connecting right now. Please check your connection or visit the [FAQ & Help](/faq/) page.");
            console.error('AI Assistant Error:', err);
        });
    }

    sendBtn.addEventListener('click', () => sendMessage());

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Quick prompt buttons
    document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const prompt = btn.getAttribute('data-prompt');
            if (prompt) {
                sendMessage(prompt);
            }
        });
    });

    function appendMessage(sender, text, meta = {}) {
        const bubble = document.createElement('div');
        bubble.className = sender === 'user' ? 'chat-bubble chat-bubble-user' : 'chat-bubble chat-bubble-ai';

        // Format Markdown simple bold and bullets
        const formattedText = formatMarkdown(text);
        bubble.innerHTML = formattedText;

        // If AI, add source tag and feedback buttons
        if (sender === 'ai') {
            const footer = document.createElement('div');
            footer.className = 'd-flex justify-content-between align-items-center mt-2 pt-1 border-top small text-muted';
            
            const sourceBadge = document.createElement('span');
            sourceBadge.className = 'badge bg-light text-secondary border';
            sourceBadge.innerText = meta.source ? `Source: ${formatSource(meta.source)}` : 'Fitora Assistant';
            footer.appendChild(sourceBadge);

            const feedbackGroup = document.createElement('div');
            feedbackGroup.className = 'btn-group btn-group-sm';
            
            const thumbUp = document.createElement('button');
            thumbUp.className = 'btn btn-outline-secondary btn-sm py-0 px-1';
            thumbUp.innerHTML = '<i class="bi bi-hand-thumbs-up"></i>';
            thumbUp.title = 'Helpful';
            thumbUp.onclick = () => submitFeedback(conversationId, 'helpful', thumbUp, thumbDown);

            const thumbDown = document.createElement('button');
            thumbDown.className = 'btn btn-outline-secondary btn-sm py-0 px-1';
            thumbDown.innerHTML = '<i class="bi bi-hand-thumbs-down"></i>';
            thumbDown.title = 'Unhelpful';
            thumbDown.onclick = () => submitFeedback(conversationId, 'unhelpful', thumbDown, thumbUp);

            feedbackGroup.appendChild(thumbUp);
            feedbackGroup.appendChild(thumbDown);
            footer.appendChild(feedbackGroup);

            bubble.appendChild(footer);

            // If a support ticket was created, add ticket link
            if (meta.ticket_created && meta.ticket_id) {
                const ticketNotice = document.createElement('div');
                ticketNotice.className = 'alert alert-success py-2 px-3 mt-2 mb-0 small';
                ticketNotice.innerHTML = `<i class="bi bi-ticket-perforated-fill me-1"></i> <a href="/support/tickets/" class="alert-link">View your Support Ticket (${meta.ticket_id})</a>`;
                bubble.appendChild(ticketNotice);
            }
        }

        messagesContainer.appendChild(bubble);
        scrollToBottom();
    }

    function showTypingIndicator() {
        const id = 'typing_' + Date.now();
        const indicator = document.createElement('div');
        indicator.id = id;
        indicator.className = 'chat-bubble chat-bubble-ai text-muted py-2 px-3 small';
        indicator.innerHTML = '<span class="spinner-grow spinner-grow-sm text-teal me-2" role="status"></span> Fitora AI is thinking...';
        messagesContainer.appendChild(indicator);
        scrollToBottom();
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function submitFeedback(convId, rating, activeBtn, inactiveBtn) {
        activeBtn.classList.remove('btn-outline-secondary');
        activeBtn.classList.add(rating === 'helpful' ? 'btn-success' : 'btn-danger');
        inactiveBtn.disabled = true;

        fetch('/assistant/api/feedback/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                conversation_id: convId,
                rating: rating
            })
        }).catch(err => console.log('Feedback log note:', err));
    }

    function formatSource(source) {
        const map = {
            'faq_database': 'PostgreSQL FAQs',
            'error_guide': 'Error Code Guide',
            'user_nutrition': 'Live Food Diary',
            'ticket_system': 'Support Ticket Desk',
            'llm_api': 'AI Language Model',
            'fallback_faq': 'Fitora Knowledge Base'
        };
        return map[source] || source;
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let escaped = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Bold
        escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Italic
        escaped = escaped.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Inline code
        escaped = escaped.replace(/`([^`]+)`/g, '<code class="bg-light text-dark px-1 py-0 rounded">$1</code>');
        // Headings
        escaped = escaped.replace(/^### (.*$)/gim, '<h6 class="fw-bold mt-2 mb-1">$1</h6>');
        // Bullet points
        escaped = escaped.replace(/^\- (.*$)/gim, '<div class="ms-2">• $1</div>');
        // Links
        escaped = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-teal text-decoration-none fw-semibold">$1</a>');
        // Linebreaks
        escaped = escaped.replace(/\n/g, '<br>');

        return escaped;
    }

    function getCsrfToken() {
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }
});
