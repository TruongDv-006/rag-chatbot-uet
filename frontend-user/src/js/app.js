/**
 * app.js – AppController: điều phối toàn bộ frontend-user
 *
 * Luồng khởi động:
 *  1. AuthService.init() – đọc token từ URL hash (SSO redirect) hoặc localStorage
 *  2. Nếu chưa auth → hiển thị authOverlay
 *  3. Nếu đã auth   → render giao diện, load sessions
 */
import { AuthService }  from './services/AuthService.js';
import { ApiService }   from './services/ApiService.js';
import { ToastService } from './services/ToastService.js';
import { ChatView }     from './views/ChatView.js';
import { CONFIG }       from './config.js';

class AppController {
    constructor() {
        this.auth    = new AuthService();
        this.toast   = new ToastService();
        this.view    = new ChatView();
        this.api     = new ApiService(this.auth);

        this.currentSessionId = null;
        this.sessions = [];
        this.isSending = false;

        this._init();
    }

    /* ============================================================
       KHỞI ĐỘNG
    ============================================================ */
    async _init() {
        // Đọc token từ URL hash (SSO flow) hoặc localStorage
        this.auth.init();

        if (!this.auth.isAuthenticated()) {
            this._showAuthWall();
            return;
        }

        // Hiển thị app
        this.view.showApp();
        this.view.setUserInfo(this.auth.getUsername());

        // Bind events
        this._bindEvents();

        // Load sidebar sessions
        await this._loadSessions();

        this.toast.success(`Xin chào, ${this.auth.getUsername()}! 👋`);
    }

    /* ============================================================
       AUTH WALL
    ============================================================ */
    _showAuthWall() {
        this.view.showAuth();
        document.getElementById('goToLoginBtn').href = `${CONFIG.LOGIN_PAGE_URL}/#logout=true`;
    }

    /* ============================================================
       BIND EVENTS
    ============================================================ */
    _bindEvents() {
        // Sidebar toggle (mobile)
        document.getElementById('openSidebarBtn').addEventListener('click', () => this.view.openSidebar());
        document.getElementById('closeSidebarBtn').addEventListener('click', () => this.view.closeSidebar());
        document.getElementById('sidebarOverlay').addEventListener('click', () => this.view.closeSidebar());

        // New chat
        document.getElementById('newChatBtn').addEventListener('click', () => this._startNewChat());

        // Clear chat
        document.getElementById('clearChatBtn').addEventListener('click', () => this._confirmClearChat());

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => this._confirmLogout());

        // Send message
        this.view.bindSendMessage(() => this._handleSend());

        // Suggestion cards
        this.view.bindSuggestions((question) => this._fillAndSend(question));
    }

    /* ============================================================
       SESSIONS
    ============================================================ */
    async _loadSessions() {
        try {
            this.sessions = await this.api.getSessions();
            this.view.renderSessions(this.sessions, this.currentSessionId, (id) => this._loadSession(id));
        } catch (err) {
            this.toast.error('Không thể tải lịch sử hội thoại.');
        }
    }

    async _loadSession(sessionId) {
        this.view.closeSidebar();
        this.currentSessionId = sessionId;
        this.view.setActiveSession(sessionId);
        this.view.clearMessages();
        this.view.showChatBox();

        const session = this.sessions.find(s => s.id === sessionId);
        this.view.setTopbarTitle(session?.title ?? 'Hội thoại cũ');

        try {
            const messages = await this.api.getSessionMessages(sessionId);
            if (Array.isArray(messages) && messages.length > 0) {
                messages.forEach(m => {
                    this.view.appendMessage(m.role, m.content, m.sources ?? [], m.created_at ? new Date(m.created_at).toLocaleTimeString('vi-VN', {hour:'2-digit',minute:'2-digit'}) : null);
                });
            } else {
                this.view.showWelcome();
            }
        } catch {
            this.toast.error('Không tải được tin nhắn của phiên này.');
        }
    }

    /* ============================================================
       NEW CHAT
    ============================================================ */
    _startNewChat() {
        this.currentSessionId = null;
        this.view.clearMessages();
        this.view.showWelcome();
        this.view.setTopbarTitle('Cuộc trò chuyện mới');
        this.view.setActiveSession(null);
        this.view.closeSidebar();
    }

    /* ============================================================
       SEND MESSAGE
    ============================================================ */
    async _handleSend() {
        if (this.isSending) return;
        const text = this.view.getInputValue();
        if (!text) return;

        this.isSending = true;
        this.view.clearInput();
        this.view.appendMessage('user', text);
        this.view.showTyping();

        try {
            const data = await this.api.sendChat(text, this.currentSessionId);

            this.view.hideTyping();

            // Nếu backend tạo session mới → lưu lại
            if (data.session_id && !this.currentSessionId) {
                this.currentSessionId = data.session_id;
                const title = text.length > 40 ? text.slice(0, 40) + '…' : text;
                this.view.setTopbarTitle(title);
                // Reload sidebar để thấy session mới
                await this._loadSessions();
                this.view.setActiveSession(this.currentSessionId);
            }

            this.view.appendMessage('bot', data.answer ?? data.response ?? 'Không có phản hồi.', data.sources ?? []);

        } catch (err) {
            this.view.hideTyping();
            this.view.appendMessage('bot', `⚠️ Lỗi: ${err.message}`);
            this.toast.error(err.message);
        } finally {
            this.isSending = false;
        }
    }

    /** Điền câu hỏi suggestion vào input và gửi ngay */
    _fillAndSend(question) {
        const input = document.getElementById('userInput');
        input.value = question;
        input.dispatchEvent(new Event('input'));
        this._handleSend();
    }

    /* ============================================================
       CLEAR / LOGOUT
    ============================================================ */
    async _confirmClearChat() {
        if (!this.currentSessionId && this.view.chatBox.children.length === 0) return;
        const ok = await this.view.showConfirm(
            'Xoá cuộc trò chuyện',
            'Thao tác này sẽ xoá toàn bộ tin nhắn trên màn hình. Bạn có muốn tiếp tục?'
        );
        if (ok) this._startNewChat();
    }

    _confirmLogout() {
        this.auth.clearToken();
        this.auth.redirectToLogin();
    }
}

/* ============================================================
   KHỞI CHẠY KHI DOM SẴN SÀNG
============================================================ */
document.addEventListener('DOMContentLoaded', () => {
    new AppController();
});