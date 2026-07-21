/**
 * ApiService.js – Toàn bộ HTTP calls cho Admin
 * Backend routes:
 *   POST /api/v1/admin/upload-doc         – Upload tài liệu
 *   GET  /api/v1/admin/documents          – Danh sách tài liệu (mocked nếu chưa có)
 *   GET  /api/v1/admin/users              – Danh sách người dùng
 *   GET  /api/v1/admin/stats              – Thống kê tổng quan
 *   GET  /api/v1/admin/tasks              – Danh sách tasks Celery
 */
import { CONFIG } from '../config.js';

export class ApiService {
    constructor(authService) {
        this.auth    = authService;
        this.baseUrl = CONFIG.BASE_URL;
    }

    _headers() {
        return { 'Authorization': `Bearer ${this.auth.getToken()}` };
    }

    async _json(res) {
        if (res.status === 401) { this.auth.clearToken(); this.auth.redirectToLogin(); throw new Error('Phiên hết hạn'); }
        if (res.status === 403) throw new Error('Không có quyền truy cập');
        if (!res.ok) {
            const e = await res.json().catch(() => ({}));
            throw new Error(e.detail ?? `Lỗi ${res.status}`);
        }
        return res.json();
    }

    /** Upload file PDF/DOCX – dùng FormData */
    async uploadDocument(file, onProgress) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);

            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${this.baseUrl}/admin/upload-doc`);
            xhr.setRequestHeader('Authorization', `Bearer ${this.auth.getToken()}`);

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100));
            };
            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                   resolve(JSON.parse(xhr.responseText));
                } else {
                    try { reject(new Error(JSON.parse(xhr.responseText).detail ?? 'Upload thất bại')); }
                    catch { reject(new Error('Upload thất bại')); }
                }
            };
            xhr.onerror = () => reject(new Error('Lỗi mạng'));
            xhr.send(formData);
        });
    }

    /** Lấy thống kê hệ thống */
    async getStats() {
        const res = await fetch(`${this.baseUrl}/admin/stats`, { headers: this._headers() });
        return this._json(res);
    }

    /** Lấy danh sách tài liệu */
    async getDocuments() {
        const res = await fetch(`${this.baseUrl}/admin/documents`, { headers: this._headers() });
        return this._json(res);
    }

    /** Xóa tài liệu */
    async deleteDocument(docName) {
        const res = await fetch(`${this.baseUrl}/admin/documents/${encodeURIComponent(docName)}`, {
            method: 'DELETE', headers: this._headers()
        });
        return this._json(res);
    }

    /** Lấy danh sách người dùng */
    async getUsers() {
        const res = await fetch(`${this.baseUrl}/admin/users`, { headers: this._headers() });
        return this._json(res);
    }

    /** Cập nhật thông tin người dùng */
    async updateUser(userId, data) {
        const res = await fetch(`${this.baseUrl}/admin/users/${userId}`, {
            method: 'PUT',
            headers: { ...this._headers(), 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return this._json(res);
    }

    /** Xóa người dùng */
    async deleteUser(userId) {
        const res = await fetch(`${this.baseUrl}/admin/users/${userId}`, {
            method: 'DELETE',
            headers: this._headers()
        });
        return this._json(res);
    }

    /** Lấy danh sách tasks từ Celery/Redis */
    async getTasks() {
        const res = await fetch(`${this.baseUrl}/admin/tasks`, { headers: this._headers() });
        return this._json(res);
    }
}