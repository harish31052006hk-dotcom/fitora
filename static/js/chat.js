/* Fitora AI — shared, resilient chat for the floating widget and full-page assistant. */
document.addEventListener('DOMContentLoaded', () => {
    const getConversationId = () => {
        let id = sessionStorage.getItem('fitora_conv_id');
        if (!id) {
            id = `conv_${Math.random().toString(36).slice(2, 11)}_${Date.now()}`;
            sessionStorage.setItem('fitora_conv_id', id);
        }
        return id;
    };
    const conversationId = getConversationId();

    const csrfToken = () => {
        const item = document.cookie.split('; ').find(row => row.trim().startsWith('csrftoken='));
        return item ? decodeURIComponent(item.trim().slice('csrftoken='.length)) : '';
    };

    const escapeHTML = value => String(value ?? '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');

    function formatMarkdown(value) {
        let result = escapeHTML(value);
        result = result.replace(/^### (.*)$/gm, '<h6 class="response-heading">$1</h6>');
        result = result.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        result = result.replace(/(^|[^*])\*(.*?)\*/g, '$1<em>$2</em>');
        result = result.replace(/`([^`]+)`/g, '<code>$1</code>');
        result = result.replace(/^[-•] (.*)$/gm, '<div class="response-list-item">$1</div>');
        result = result.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+|\/[^)\s]*)\)/g,
            '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        return result.replace(/\n/g, '<br>');
    }

    function initChat(options) {
        const input = document.getElementById(options.inputId);
        const sendBtn = document.getElementById(options.sendId);
        const messages = document.getElementById(options.messagesId);
        const fileInput = document.getElementById(options.fileId);
        const attachBtn = document.getElementById(options.attachId);
        const preview = document.getElementById(options.previewId);
        if (!input || !sendBtn || !messages) return;

        let selectedFile = null;
        let selectedDataUrl = null;
        let requestInProgress = false;
        const history = [];

        const scrollBottom = () => { messages.scrollTop = messages.scrollHeight; };
        const showTyping = () => {
            const element = document.createElement('div');
            element.className = 'chat-bubble chat-bubble-ai chat-typing';
            element.innerHTML = '<span class="typing-dots" aria-hidden="true"><i></i><i></i><i></i></span><span>Fitora is thinking</span>';
            element.setAttribute('aria-live', 'polite');
            messages.appendChild(element);
            scrollBottom();
            return element;
        };

        function appendMessage(sender, text, meta = {}, imageUrl = null) {
            const bubble = document.createElement('div');
            bubble.className = sender === 'user' ? 'chat-bubble chat-bubble-user' : 'chat-bubble chat-bubble-ai';
            if (imageUrl && sender === 'user') {
                const image = document.createElement('img');
                image.className = 'chat-attachment-preview';
                image.src = imageUrl;
                image.alt = 'Image attached to your message';
                bubble.appendChild(image);
            }
            if (text) {
                const content = document.createElement('div');
                content.className = 'chat-response-content';
                content.innerHTML = formatMarkdown(text);
                bubble.appendChild(content);
            }
            if (sender === 'ai') {
                const footer = document.createElement('div');
                footer.className = 'chat-message-meta';
                const source = document.createElement('span');
                source.className = 'chat-source-label';
                source.textContent = meta.source ? `Fitora · ${formatSource(meta.source)}` : 'Fitora AI';
                footer.appendChild(source);
                if (meta.ticket_created && meta.ticket_id) {
                    const ticket = document.createElement('a');
                    ticket.href = '/support/tickets/';
                    ticket.className = 'chat-ticket-link';
                    ticket.textContent = `Ticket ${meta.ticket_id} created · View tickets`;
                    footer.appendChild(ticket);
                }
                bubble.appendChild(footer);
            }
            messages.appendChild(bubble);
            scrollBottom();
        }

        function resetImage() {
            selectedFile = null;
            selectedDataUrl = null;
            if (fileInput) fileInput.value = '';
            if (preview) {
                preview.hidden = true;
                preview.replaceChildren();
            }
        }

        if (attachBtn && fileInput) {
            attachBtn.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', () => {
                const file = fileInput.files && fileInput.files[0];
                if (!file) return;
                const accepted = ['image/jpeg', 'image/png', 'image/webp'];
                if (!accepted.includes(file.type)) {
                    appendMessage('ai', 'Please attach a JPEG, PNG, or WebP image.');
                    resetImage();
                    return;
                }
                if (file.size > 4 * 1024 * 1024) {
                    appendMessage('ai', 'That image is larger than 4 MB. Please choose a smaller image.');
                    resetImage();
                    return;
                }
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = () => {
                    selectedDataUrl = typeof reader.result === 'string' ? reader.result : null;
                    if (preview && selectedDataUrl) {
                        const image = document.createElement('img');
                        image.src = selectedDataUrl;
                        image.alt = 'Selected image';
                        image.className = 'chat-selected-image';
                        const label = document.createElement('span');
                        label.textContent = file.name;
                        const remove = document.createElement('button');
                        remove.type = 'button';
                        remove.className = 'chat-remove-image';
                        remove.setAttribute('aria-label', 'Remove attached image');
                        remove.textContent = '×';
                        remove.addEventListener('click', resetImage);
                        preview.replaceChildren(image, label, remove);
                        preview.hidden = false;
                    }
                };
                reader.onerror = () => {
                    resetImage();
                    appendMessage('ai', 'I could not read that image. Please select it again.');
                };
                reader.readAsDataURL(file);
            });
        }

        async function sendMessage(suggestedText = null) {
            if (requestInProgress) return;
            const text = typeof suggestedText === 'string' ? suggestedText.trim() : input.value.trim();
            if (!text && !selectedFile) return;
            if (selectedFile && !selectedDataUrl) {
                appendMessage('ai', 'Your image is still loading. Please try again in a moment.');
                return;
            }

            const imageForBubble = selectedDataUrl;
            appendMessage('user', text || 'Please analyze this image.', {}, imageForBubble);
            input.value = '';
            requestInProgress = true;
            sendBtn.disabled = true;
            input.disabled = true;
            if (attachBtn) attachBtn.disabled = true;
            const typing = showTyping();
            const controller = new AbortController();
            const timer = window.setTimeout(() => controller.abort(), 45000);

            try {
                const body = {
                    message: text,
                    conversation_id: conversationId,
                    page: window.location.pathname,
                    history: history.slice(-8)
                };
                if (selectedDataUrl) body.image_data = selectedDataUrl;
                const response = await fetch('/assistant/api/chat/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
                    body: JSON.stringify(body),
                    signal: controller.signal
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) throw new Error(data.error || `The service returned HTTP ${response.status}.`);
                if (!data.response) throw new Error(data.error || 'The AI service returned an empty response.');
                history.push({ role: 'user', content: text || '[Image attached for analysis]' });
                history.push({ role: 'assistant', content: data.response });
                if (history.length > 10) history.splice(0, history.length - 10);
                appendMessage('ai', data.response, data);
            } catch (error) {
                const message = error.name === 'AbortError'
                    ? 'This request took too long. Please retry with a shorter question or a smaller image.'
                    : (error.message || 'I could not reach Fitora AI. Please try again.');
                appendMessage('ai', `${message}\n\nYou can also visit [FAQ & Help](/faq/) while the service recovers.`);
                console.error('Fitora AI request failed:', error.name || 'Error');
            } finally {
                window.clearTimeout(timer);
                typing.remove();
                resetImage();
                requestInProgress = false;
                sendBtn.disabled = false;
                input.disabled = false;
                if (attachBtn) attachBtn.disabled = false;
                input.focus();
            }
        }

        sendBtn.addEventListener('click', () => sendMessage());
        input.addEventListener('keydown', event => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
        document.querySelectorAll(options.promptSelector).forEach(button => {
            button.addEventListener('click', () => {
                const prompt = button.getAttribute('data-prompt');
                if (prompt) {
                    if (options.fullPage) sendMessage(prompt);
                    else {
                        const chat = document.getElementById('fitoraChatWindow');
                        if (chat) { chat.style.display = 'flex'; chat.classList.remove('d-none'); }
                        sendMessage(prompt);
                    }
                }
            });
        });
    }

    function formatSource(source) {
        const labels = {
            faq_database: 'Knowledge base', error_guide: 'Error guide',
            user_nutrition: 'Food diary', ticket_system: 'Support desk',
            llm_api: 'AI model', fallback_faq: 'Knowledge base', system: 'Fitora'
        };
        return labels[source] || source;
    }

    const trigger = document.getElementById('fitoraAiTrigger');
    const chatWindow = document.getElementById('fitoraChatWindow');
    const closeBtn = document.getElementById('chatCloseBtn');
    if (trigger && chatWindow) {
        trigger.addEventListener('click', event => {
            event.preventDefault();
            const opening = chatWindow.style.display === 'none' || chatWindow.classList.contains('d-none');
            chatWindow.style.display = opening ? 'flex' : 'none';
            chatWindow.classList.toggle('d-none', !opening);
            if (opening) document.getElementById('chatInput')?.focus();
        });
        closeBtn?.addEventListener('click', () => { chatWindow.style.display = 'none'; chatWindow.classList.add('d-none'); });
        initChat({ inputId: 'chatInput', sendId: 'chatSendBtn', messagesId: 'chatMessages', fileId: 'chatImageInput', attachId: 'chatAttachBtn', previewId: 'chatImagePreview', promptSelector: '.quick-prompt-btn', fullPage: false });
    }
    initChat({ inputId: 'fullChatInput', sendId: 'fullChatSendBtn', messagesId: 'fullChatMessages', fileId: 'fullChatImageInput', attachId: 'fullChatAttachBtn', previewId: 'fullChatImagePreview', promptSelector: '.full-prompt-btn', fullPage: true });
});
