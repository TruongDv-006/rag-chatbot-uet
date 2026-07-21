/**
 * config.js – Cấu hình toàn cục cho frontend-user
 * Khi chạy qua Nginx, BASE_URL = '/api/v1' (Nginx proxy sang backend)
 * Khi dev local trực tiếp, đổi thành 'http://localhost:8000/api/v1'
 */
export const CONFIG = {
    BASE_URL:      'http://localhost:8000/api/v1',
    LOGIN_PAGE_URL: 'http://localhost:5000',
    TOKEN_KEY: 'uet_access_token',
    USER_KEY:  'uet_user_info',
};
