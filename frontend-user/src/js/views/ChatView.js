/**
 * ChatView.js – Quản lý toàn bộ DOM rendering của màn hình chat
 */
export class ChatView {
    constructor() {
        // Core panels
        this.authOverlay    = document.getElementById('authOverlay');
        this.appLayout      = document.getElementById('appLayout');

        // Sidebar
        this.sidebar        = document.getElementById('sidebar');
        this.sidebarOverlay = document.getElementById('sidebarOverlay');
        this.sessionsList   = document.getElementById('sessionsList');
        this.userAvatar     = document.getElementById('userAvatar');
        this.userName       = document.getElementById('userName');

        // Chat area
        this.welcomeScreen   = document.getElementById('welcomeScreen');
        this.chatBox         = document.getElementById('chatBox');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.topbarTitle     = document.getElementById('topbarTitle').querySelector('span');

        // Input
        this.userInput  = document.getElementById('userInput');
        this.sendBtn    = document.getElementById('sendBtn');
        this.charCount  = document.getElementById('charCount');

        // Modal
        this.confirmModal  = document.getElementById('confirmModal');
        this.modalTitle    = document.getElementById('modalTitle');
        this.modalDesc     = document.getElementById('modalDesc');
        this.modalConfirmBtn = document.getElementById('modalConfirmBtn');
        this.modalCancelBtn  = document.getElementById('modalCancelBtn');

        this._setupTextareaAutoResize();
    }

    /* ======= AUTH ======= */
    showAuth() {
        this.authOverlay.classList.remove('hidden');
        this.appLayout.classList.add('hidden');
    }
    showApp() {
        this.authOverlay.classList.add('hidden');
        this.appLayout.classList.remove('hidden');
    }

    /* ======= USER INFO ======= */
    setUserInfo(username) {
        this.userName.textContent = username;
        this.userAvatar.textContent = username.charAt(0).toUpperCase();
    }

    /* ======= SIDEBAR ======= */
    openSidebar() {
        this.sidebar.classList.add('open');
        this.sidebarOverlay.classList.add('show');
    }
    closeSidebar() {
        this.sidebar.classList.remove('open');
        this.sidebarOverlay.classList.remove('show');
    }

    /** Render danh sách sessions vào sidebar */
    renderSessions(sessions, activeId, onSelect) {
        if (!sessions || sessions.length === 0) {
            this.sessionsList.innerHTML = `
                <div class="sessions-empty">
                    <i class="fas fa-comment-slash"></i>
                    Chưa có lịch sử trò chuyện
                </div>`;
            return;
        }
        this.sessionsList.innerHTML = sessions.map(s => `
            <div class="session-item ${s.id === activeId ? 'active' : ''}" data-id="${s.id}">
                <div class="session-icon"><i class="fas fa-message"></i></div>
                <div class="session-info">
                    <div class="session-title">${this._escapeHtml(s.title ?? 'Cuộc trò chuyện')}</div>
                    <div class="session-meta">${this._formatDate(s.created_at)}</div>
                </div>
            </div>`).join('');

        this.sessionsList.querySelectorAll('.session-item').forEach(el => {
            el.addEventListener('click', () => onSelect(Number(el.dataset.id)));
        });
    }

    setActiveSession(sessionId) {
        this.sessionsList.querySelectorAll('.session-item').forEach(el => {
            el.classList.toggle('active', Number(el.dataset.id) === sessionId);
        });
    }

    /* ======= WELCOME / CHAT SCREEN ======= */
    showWelcome() {
        this.welcomeScreen.classList.remove('hidden');
        this.chatBox.classList.add('hidden');
    }
    showChatBox() {
        this.welcomeScreen.classList.add('hidden');
        this.chatBox.classList.remove('hidden');
    }

    setTopbarTitle(text) {
        this.topbarTitle.textContent = text;
    }

    /* ======= MESSAGES ======= */
    clearMessages() {
        this.chatBox.innerHTML = '';
    }

    /**
     * Render một tin nhắn vào chatBox
     * @param {'user'|'bot'} role
     * @param {string} content
     * @param {Array}  sources
     * @param {string} time
     */
    appendMessage(role, content, sources = [], time = null) {
        this.showChatBox();
        const isBot = role === 'bot' || role === 'assistant';
        const roleClass = isBot ? 'bot' : 'user';

        const avatarIcon = isBot ? 'fa-robot' : 'fa-user';
        const timeStr = time ?? this._nowTime();

        // Render markdown cho bot, escape HTML cho user
        const bubbleHtml = isBot
            ? (typeof marked !== 'undefined' ? marked.parse(content) : this._escapeHtml(content))
            : this._escapeHtml(content);

        // Build sources HTML
        let sourcesHtml = '';
        if (isBot && sources && sources.length > 0) {
            const items = sources.map(s =>
                `<div class="source-item"><i class="fas fa-bookmark"></i> ${this._escapeHtml(s.document_name)} – Trang ${s.page ?? '?'}</div>`
            ).join('');
            sourcesHtml = `
                <div class="sources-box">
                    <div class="sources-title"><i class="fas fa-book-open"></i> Nguồn trích dẫn</div>
                    ${items}
                </div>`;
        }

        const div = document.createElement('div');
        div.className = `message ${roleClass}-message`;
        div.innerHTML = `
            <div class="msg-avatar"><i class="fas ${avatarIcon}"></i></div>
            <div class="msg-content">
                <div class="bubble">${bubbleHtml}</div>
                ${sourcesHtml}
                <span class="msg-time">${timeStr}</span>
            </div>`;

        this.chatBox.appendChild(div);
        this._scrollToBottom();
    }

    /* ======= TYPING INDICATOR ======= */
    showTyping() { this.typingIndicator.classList.remove('hidden'); this._scrollToBottom(); }
    hideTyping() { this.typingIndicator.classList.add('hidden'); }

    /* ======= INPUT ======= */
    getInputValue()  { return this.userInput.value.trim(); }
    clearInput()     { this.userInput.value = ''; this._updateCharCount(); this._autoResize(); this.setSendEnabled(false); }
    setSendEnabled(enabled) { this.sendBtn.disabled = !enabled; }

    bindSendMessage(handler) {
        this.sendBtn.addEventListener('click', handler);
        this.userInput.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); if (!this.sendBtn.disabled) handler(); }
        });
        this.userInput.addEventListener('input', () => {
            this._updateCharCount();
            this._autoResize();
            this.setSendEnabled(this.userInput.value.trim().length > 0);
        });
    }

    bindSuggestions(handler) {
        document.querySelectorAll('.suggestion-card').forEach(btn => {
            btn.addEventListener('click', () => handler(btn.dataset.question));
        });
    }

    /* ======= MODAL ======= */
    showConfirm(title, desc) {
        return new Promise(resolve => {
            this.modalTitle.textContent = title;
            this.modalDesc.textContent  = desc;
            this.confirmModal.classList.remove('hidden');
            const cleanup = (result) => {
                this.confirmModal.classList.add('hidden');
                resolve(result);
            };
            this.modalConfirmBtn.onclick = () => cleanup(true);
            this.modalCancelBtn.onclick  = () => cleanup(false);
        });
    }

    /* ======= PRIVATE HELPERS ======= */
    _scrollToBottom() {
        requestAnimationFrame(() => {
            this.chatBox.scrollTop = this.chatBox.scrollHeight;
            this.typingIndicator.scrollIntoView?.({ behavior: 'smooth', block: 'end' });
        });
    }

    _updateCharCount() {
        const len = this.userInput.value.length;
        this.charCount.textContent = `${len} / 2000`;
        this.charCount.style.color = len > 1800 ? '#f87171' : '';
    }

    _setupTextareaAutoResize() {
        this.userInput.addEventListener('input', () => this._autoResize());
    }

    _autoResize() {
        this.userInput.style.height = 'auto';
        this.userInput.style.height = Math.min(this.userInput.scrollHeight, 200) + 'px';
    }

    _escapeHtml(str) {
        return String(str ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    _nowTime() {
        return new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    }

    _formatDate(dateStr) {
        if (!dateStr) return '';
        try {
            return new Date(dateStr).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
        } catch { return dateStr; }
    }
}