/**
 * AuthService.js – Quản lý JWT Token và phiên đăng nhập
 * Đọc token từ:
 *   1. URL hash (khi SSO redirect sang): #token=xxx
 *   2. localStorage (khi đã lưu trước đó)
 */
import { CONFIG } from '../config.js';

export class AuthService {

    /**
     * Khởi tạo: tự động đọc token từ URL hash nếu có, rồi lưu vào localStorage
     */
    init() {
        const hash = window.location.hash;
        if (hash && hash.startsWith('#token=')) {
            const token = hash.slice('#token='.length);
            this.saveToken(token);
            // Xóa hash khỏi URL để gọn
            history.replaceState(null, '', window.location.pathname + window.location.search);
        }
    }

    /** Lưu token vào localStorage */
    saveToken(token) {
        localStorage.setItem(CONFIG.TOKEN_KEY, token);
    }

    /** Lấy token hiện tại */
    getToken() {
        return localStorage.getItem(CONFIG.TOKEN_KEY);
    }

    /** Xóa token (đăng xuất) */
    clearToken() {
        try { localStorage.clear(); sessionStorage.clear(); } catch {}
    }

    /** Kiểm tra có token hợp lệ không (chưa decode, chỉ kiểm tra tồn tại & không expired) */
    isAuthenticated() {
        const token = this.getToken();
        if (!token) return false;
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            // exp là Unix timestamp (giây)
            return payload.exp * 1000 > Date.now();
        } catch {
            return false;
        }
    }

    /** Giải mã payload từ JWT để lấy thông tin user */
    getUserInfo() {
        const token = this.getToken();
        if (!token) return null;
        try {
            return JSON.parse(atob(token.split('.')[1]));
        } catch {
            return null;
        }
    }

    /** Trả về role của user ('student' | 'admin') */
    getRole() {
        const info = this.getUserInfo();
        return info?.role ?? 'student';
    }

    /** Trả về username */
    getUsername() {
        const info = this.getUserInfo();
        return info?.sub ?? 'Sinh viên';
    }

    /** Điều hướng sang trang login SSO */
    redirectToLogin() {
        window.location.href = `${CONFIG.LOGIN_PAGE_URL}/#logout=true`;
    }
}
