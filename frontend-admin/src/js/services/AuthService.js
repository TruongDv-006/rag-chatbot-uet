/**
 * AuthService.js – Xác thực và kiểm tra role Admin
 */
import { CONFIG } from '../config.js';

export class AuthService {
    init() {
        const hash = window.location.hash;
        if (hash && hash.startsWith('#token=')) {
            const token = hash.slice('#token='.length);
            localStorage.setItem(CONFIG.TOKEN_KEY, token);
            history.replaceState(null, '', window.location.pathname);
        }
    }

    getToken()  { return localStorage.getItem(CONFIG.TOKEN_KEY); }
    clearToken(){ localStorage.removeItem(CONFIG.TOKEN_KEY); }

    isAuthenticated() {
        const token = this.getToken();
        if (!token) return false;
        try {
            const p = JSON.parse(atob(token.split('.')[1]));
            return p.exp * 1000 > Date.now();
        } catch { return false; }
    }

    getUserInfo() {
        try { return JSON.parse(atob(this.getToken().split('.')[1])); }
        catch { return null; }
    }

    getRole()     { return this.getUserInfo()?.role ?? 'student'; }
    getUsername() { return this.getUserInfo()?.sub  ?? 'Admin'; }
    isAdmin()     { return this.getRole() === 'admin'; }

    redirectToLogin() { window.location.href = CONFIG.LOGIN_PAGE_URL; }
}
