/**
 * ApiService.js – Toàn bộ lời gọi HTTP đến Backend API
 * Tự động đính kèm JWT Bearer Token vào mọi request.
 */
import { CONFIG } from '../config.js';

export class ApiService {
    constructor(authService) {
        this.authService = authService;
        this.baseUrl = CONFIG.BASE_URL;
    }

    /** Tạo headers chuẩn với Bearer token */
    _headers(extra = {}) {
        return {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.authService.getToken()}`,
            ...extra,
        };
    }

    /** Xử lý response chung – throw nếu lỗi */
    async _handleResponse(res) {
        if (res.status === 401) {
            this.authService.clearToken();
            this.authService.redirectToLogin();
            throw new Error('Phiên đăng nhập hết hạn');
        }
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail ?? `Lỗi ${res.status}`);
        }
        return res.json();
    }

    /**
     * POST /chat – Gửi tin nhắn
     * @param {string} message
     * @param {number|null} sessionId
     */
    async sendChat(message, sessionId = null) {
        const res = await fetch(`${this.baseUrl}/chat`, {
            method: 'POST',
            headers: this._headers(),
            body: JSON.stringify({ message, session_id: sessionId }),
        });
        return this._handleResponse(res);
    }

    /**
     * GET /sessions – Lấy danh sách phiên chat
     */
    async getSessions() {
        const res = await fetch(`${this.baseUrl}/sessions`, {
            headers: this._headers(),
        });
        return this._handleResponse(res);
    }

    /**
     * GET /sessions/{id}/messages – Lấy lịch sử tin nhắn của 1 phiên
     */
    async getSessionMessages(sessionId) {
        const res = await fetch(`${this.baseUrl}/sessions/${sessionId}/messages`, {
            headers: this._headers(),
        });
        return this._handleResponse(res);
    }
}