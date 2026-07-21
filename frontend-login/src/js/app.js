/**
 * app.js – Login/Register Controller
 *
 * SSO FLOW:
 *  1. User nhập username + password → POST /api/v1/auth/login
 *  2. Nhận access_token → decode JWT payload lấy role
 *  3. Lưu token vào localStorage (key: 'uet_access_token')
 *  4. Redirect có kèm #token=<jwt>:
 *       role === 'admin'   → ADMIN_URL/#token=<jwt>
 *       role === 'student' → USER_URL/#token=<jwt>
 *
 * Register flow: POST /api/v1/auth/register → tự động login
 */

/* ============================================================
   CONFIG – đổi URL theo môi trường
   - API_BASE: Login page chạy riêng (port 5000), KHÔNG qua Nginx
     nên phải gọi thẳng backend port 8000
   - USER_URL / ADMIN_URL: URL redirect sau khi đăng nhập thành công
============================================================ */
const CONFIG = {
    API_BASE:  'http://localhost:8000/api/v1',  // Gọi thẳng backend
    USER_URL:  'http://localhost:4000',          // frontend-user
    ADMIN_URL: 'http://localhost:4001',          // frontend-admin
    TOKEN_KEY: 'uet_access_token',
};

/* ============================================================
   TOAST
============================================================ */
const Toast = {
    el: null,
    init() { this.el = document.getElementById('toastContainer'); },
    show(msg, type = 'info', ms = 4000) {
        const icons = { success: 'fa-circle-check', error: 'fa-circle-xmark', info: 'fa-circle-info' };
        const t = document.createElement('div');
        t.className = `toast toast-${type}`;
        t.innerHTML = `<i class="fas ${icons[type] ?? icons.info}"></i><span>${msg}</span>`;
        this.el.appendChild(t);
        setTimeout(() => { t.classList.add('toast-out'); t.addEventListener('animationend', () => t.remove()); }, ms);
    },
    success(m) { this.show(m, 'success'); },
    error(m)   { this.show(m, 'error'); },
};

/* ============================================================
   HELPERS
============================================================ */
function decodeJwt(token) {
    try { return JSON.parse(atob(token.split('.')[1])); }
    catch { return null; }
}

function setLoading(btn, loading) {
    const text    = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.btn-spinner');
    if (text)    text.style.display    = loading ? 'none' : 'flex';
    if (spinner) spinner.style.display = loading ? 'flex' : 'none';
    btn.disabled = loading;
}

function showAlert(boxId, message, type = 'error') {
    const box = document.getElementById(boxId);
    const icons = { error: 'fa-circle-xmark', success: 'fa-circle-check', info: 'fa-circle-info' };
    box.className = `alert-box alert-${type}`;
    box.innerHTML = `<i class="fas ${icons[type]}"></i><span>${message}</span>`;
    box.classList.remove('hidden');
}

function hideAlert(boxId) {
    const box = document.getElementById(boxId);
    box.classList.add('hidden');
    box.innerHTML = '';
}

function markError(groupId, errId, msg) {
    document.getElementById(groupId)?.querySelector('.input-wrap')?.classList.add('error');
    const span = document.getElementById(errId);
    if (span) span.textContent = msg;
}

function clearErrors(...groupIds) {
    groupIds.forEach(id => {
        document.getElementById(id)?.querySelector('.input-wrap')?.classList.remove('error');
    });
}

function clearFieldErrors(...errIds) {
    errIds.forEach(id => { const el = document.getElementById(id); if (el) el.textContent = ''; });
}

/* ============================================================
   REDIRECT OVERLAY
============================================================ */
function showRedirectOverlay(role) {
    const isAdmin  = role === 'admin';
    const label    = isAdmin ? 'Admin Dashboard' : 'UET Chatbot';
    const iconCls  = isAdmin ? 'fa-shield-halved' : 'fa-robot';

    const overlay = document.createElement('div');
    overlay.className = 'redirect-overlay';
    overlay.innerHTML = `
        <div class="rd-icon"><i class="fas ${iconCls}"></i></div>
        <h3>Đăng nhập thành công!</h3>
        <p>Đang chuyển hướng đến <strong>${label}</strong>...</p>`;
    document.body.appendChild(overlay);
}

/* ============================================================
   SSO REDIRECT
============================================================ */
function redirectByRole(token) {
    const payload = decodeJwt(token);
    const role    = payload?.role ?? 'student';

    // Lưu vào localStorage để các frontend khác đọc lại
    localStorage.setItem(CONFIG.TOKEN_KEY, token);

    showRedirectOverlay(role);

    const dest = role === 'admin' ? CONFIG.ADMIN_URL : CONFIG.USER_URL;

    setTimeout(() => {
        window.location.href = `${dest}/#token=${encodeURIComponent(token)}`;
    }, 1200);
}

/* ============================================================
   API CALLS & ERROR FORMATTING
============================================================ */
function formatApiError(detail, status) {
    if (!detail) return `Lỗi ${status}`;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        return detail.map(err => {
            const field = err.loc ? err.loc[err.loc.length - 1] : '';
            const msg = err.msg || 'Dữ liệu không hợp lệ';
            if (msg.includes('value is not a valid email address')) return 'Email không đúng định dạng';
            return field ? `${field}: ${msg}` : msg;
        }).join('; ');
    }
    if (typeof detail === 'object') {
        return detail.msg || detail.message || JSON.stringify(detail);
    }
    return String(detail);
}

async function apiLogin(username, password) {
    const res = await fetch(`${CONFIG.API_BASE}/auth/login`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(formatApiError(data.detail, res.status));
    return data.access_token;
}

async function apiRegister(payload) {
    const res = await fetch(`${CONFIG.API_BASE}/auth/register`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(formatApiError(data.detail, res.status));
    return data;
}

/* ============================================================
   VALIDATE
============================================================ */
function validateLogin(username, password) {
    let ok = true;
    clearErrors('lg-username-group', 'lg-password-group');
    clearFieldErrors('lg-username-err', 'lg-password-err');

    if (!username) { markError('lg-username-group', 'lg-username-err', 'Vui lòng nhập tên đăng nhập'); ok = false; }
    if (!password) { markError('lg-password-group', 'lg-password-err', 'Vui lòng nhập mật khẩu'); ok = false; }
    return ok;
}

function validateRegister(data) {
    let ok = true;
    clearErrors('rg-fullname-group', 'rg-username-group', 'rg-email-group', 'rg-password-group', 'rg-confirm-password-group');
    clearFieldErrors('rg-fullname-err', 'rg-username-err', 'rg-email-err', 'rg-password-err', 'rg-confirm-password-err');

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!data.full_name.trim()) { markError('rg-fullname-group', 'rg-fullname-err', 'Vui lòng nhập họ và tên'); ok = false; }
    if (!data.username.trim())  { markError('rg-username-group', 'rg-username-err', 'Vui lòng nhập tên đăng nhập'); ok = false; }
    if (!emailRegex.test(data.email.trim())) { markError('rg-email-group', 'rg-email-err', 'Email không hợp lệ (ví dụ: name@example.com)'); ok = false; }
    if (data.password.length < 8) { markError('rg-password-group', 'rg-password-err', 'Mật khẩu ít nhất 8 ký tự'); ok = false; }
    if (!data.confirm_password) {
        markError('rg-confirm-password-group', 'rg-confirm-password-err', 'Vui lòng nhập lại mật khẩu');
        ok = false;
    } else if (data.password !== data.confirm_password) {
        markError('rg-confirm-password-group', 'rg-confirm-password-err', 'Mật khẩu nhập lại không khớp');
        ok = false;
    }
    return ok;
}

/* ============================================================
   PASSWORD STRENGTH
============================================================ */
function checkStrength(password) {
    let score = 0;
    if (password.length >= 8)  score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    const labels = ['', 'Yếu', 'Trung bình', 'Khá mạnh', 'Mạnh'];
    const classes = ['', 'weak', 'fair', 'good', 'strong'];

    ['bar1','bar2','bar3','bar4'].forEach((id, i) => {
        const bar = document.getElementById(id);
        bar.className = 'bar';
        if (i < score) bar.classList.add(classes[score]);
    });
    document.getElementById('strengthLabel').textContent = password ? (labels[score] || 'Yếu') : 'Nhập mật khẩu';
}

/* ============================================================
   TABS
============================================================ */
function initTabs() {
    const tabs      = document.querySelectorAll('.tab-btn');
    const slider    = document.getElementById('tabSlider');
    const loginForm = document.getElementById('loginForm');
    const regForm   = document.getElementById('registerForm');

    function activate(tabEl) {
        tabs.forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
        tabEl.classList.add('active');
        tabEl.setAttribute('aria-selected', 'true');

        const isLogin = tabEl.dataset.tab === 'login';
        // Dùng style.display trực tiếp – đảm bảo hoạt động dù CSS có xung đột
        loginForm.style.display = isLogin ? 'flex' : 'none';
        regForm.style.display   = isLogin ? 'none' : 'flex';

        // Di chuyển slider đến tab đang active
        const rect   = tabEl.getBoundingClientRect();
        const parent = tabEl.closest('.tab-switcher').getBoundingClientRect();
        slider.style.left  = (rect.left - parent.left) + 'px';
        slider.style.width = rect.width + 'px';

        hideAlert('loginAlert'); hideAlert('registerAlert');
    }

    tabs.forEach(t => t.addEventListener('click', () => activate(t)));

    // Khởi tạo vị trí slider sau khi DOM render xong
    requestAnimationFrame(() => {
        const active = document.querySelector('.tab-btn.active');
        if (active) activate(active);
    });
}

/* ============================================================
   TOGGLE PASSWORD VISIBILITY
============================================================ */
function initPasswordToggles() {
    document.querySelectorAll('.toggle-pass').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = document.getElementById(btn.dataset.target);
            const icon  = btn.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'fas fa-eye';
            } else {
                input.type = 'password';
                icon.className = 'fas fa-eye-slash';
            }
        });
    });
}

/* ============================================================
   LOGIN HANDLER
============================================================ */
async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('lgUsername').value.trim();
    const password = document.getElementById('lgPassword').value;

    if (!validateLogin(username, password)) return;

    const btn = document.getElementById('loginBtn');
    setLoading(btn, true);
    hideAlert('loginAlert');

    try {
        const token = await apiLogin(username, password);
        redirectByRole(token);
    } catch (err) {
        setLoading(btn, false);
        showAlert('loginAlert', err.message, 'error');
        Toast.error(err.message);
    }
}

/* ============================================================
   REGISTER HANDLER
============================================================ */
async function handleRegister(e) {
    e.preventDefault();

    const data = {
        full_name:        document.getElementById('rgFullname').value.trim(),
        username:         document.getElementById('rgUsername').value.trim(),
        email:            document.getElementById('rgEmail').value.trim(),
        password:         document.getElementById('rgPassword').value,
        confirm_password: document.getElementById('rgConfirmPassword').value,
    };

    if (!validateRegister(data)) return;

    const btn = document.getElementById('registerBtn');
    setLoading(btn, true);
    hideAlert('registerAlert');

    try {
        await apiRegister({
            full_name: data.full_name,
            username:  data.username,
            email:     data.email,
            password:  data.password,
        });

        showAlert('registerAlert', 'Đăng ký thành công! Đang tự động đăng nhập...', 'success');

        // Auto login sau khi đăng ký
        const token = await apiLogin(data.username, data.password);
        redirectByRole(token);

    } catch (err) {
        setLoading(btn, false);
        showAlert('registerAlert', err.message, 'error');
        Toast.error(err.message);
    }
}

/* ============================================================
   INIT
============================================================ */
document.addEventListener('DOMContentLoaded', () => {
    Toast.init();
    initTabs();
    initPasswordToggles();

    document.getElementById('loginForm')?.addEventListener('submit', handleLogin);
    document.getElementById('registerForm')?.addEventListener('submit', handleRegister);

    // Password strength meter
    document.getElementById('rgPassword')?.addEventListener('input', (e) => {
        checkStrength(e.target.value);
        const confirmVal = document.getElementById('rgConfirmPassword')?.value;
        if (confirmVal) {
            if (e.target.value !== confirmVal) {
                markError('rg-confirm-password-group', 'rg-confirm-password-err', 'Mật khẩu nhập lại không khớp');
            } else {
                clearErrors('rg-confirm-password-group');
                clearFieldErrors('rg-confirm-password-err');
            }
        }
    });

    // Realtime confirm password matching check
    document.getElementById('rgConfirmPassword')?.addEventListener('input', (e) => {
        const passVal = document.getElementById('rgPassword')?.value;
        if (e.target.value && e.target.value !== passVal) {
            markError('rg-confirm-password-group', 'rg-confirm-password-err', 'Mật khẩu nhập lại không khớp');
        } else {
            clearErrors('rg-confirm-password-group');
            clearFieldErrors('rg-confirm-password-err');
        }
    });

    // Luôn dọn dẹp storage cũ khi trang Login được mở
    try {
        localStorage.clear();
        sessionStorage.clear();
    } catch {}
});
