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
============================================================ */
const CONFIG = {
    API_BASE:   '/api/v1',           // Nginx proxy → backend
    USER_URL:   'http://localhost:3000',   // frontend-user
    ADMIN_URL:  'http://localhost:3001',   // frontend-admin
    TOKEN_KEY:  'uet_access_token',
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
    btn.querySelector('.btn-text').classList.toggle('hidden', loading);
    btn.querySelector('.btn-spinner').classList.toggle('hidden', !loading);
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
   API CALLS
============================================================ */
async function apiLogin(username, password) {
    const res = await fetch(`${CONFIG.API_BASE}/auth/login`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ username, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail ?? `Lỗi ${res.status}`);
    return data.access_token;
}

async function apiRegister(payload) {
    const res = await fetch(`${CONFIG.API_BASE}/auth/register`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail ?? `Lỗi ${res.status}`);
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
    clearErrors('rg-fullname-group', 'rg-username-group', 'rg-email-group', 'rg-password-group');
    clearFieldErrors('rg-fullname-err', 'rg-username-err', 'rg-email-err', 'rg-password-err');

    if (!data.full_name.trim()) { markError('rg-fullname-group', 'rg-fullname-err', 'Vui lòng nhập họ và tên'); ok = false; }
    if (!data.username.trim())  { markError('rg-username-group', 'rg-username-err', 'Vui lòng nhập tên đăng nhập'); ok = false; }
    if (!data.email.includes('@')) { markError('rg-email-group', 'rg-email-err', 'Email không hợp lệ'); ok = false; }
    if (data.password.length < 8) { markError('rg-password-group', 'rg-password-err', 'Mật khẩu ít nhất 8 ký tự'); ok = false; }
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

        const rect = tabEl.getBoundingClientRect();
        const parent = tabEl.closest('.tab-switcher').getBoundingClientRect();
        slider.style.left  = (rect.left - parent.left + 4) + 'px'; // offset for padding
        slider.style.width = (rect.width - 0) + 'px';

        const isLogin = tabEl.dataset.tab === 'login';
        loginForm.classList.toggle('hidden', !isLogin);
        regForm.classList.toggle('hidden', isLogin);

        // Clear alerts on switch
        hideAlert('loginAlert'); hideAlert('registerAlert');
    }

    tabs.forEach(t => t.addEventListener('click', () => activate(t)));

    // Initial slider position
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
        full_name: document.getElementById('rgFullname').value.trim(),
        username:  document.getElementById('rgUsername').value.trim(),
        email:     document.getElementById('rgEmail').value.trim(),
        password:  document.getElementById('rgPassword').value,
    };

    if (!validateRegister(data)) return;

    const btn = document.getElementById('registerBtn');
    setLoading(btn, true);
    hideAlert('registerAlert');

    try {
        await apiRegister(data);

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

    document.getElementById('loginForm').addEventListener('submit', handleLogin);
    document.getElementById('registerForm').addEventListener('submit', handleRegister);

    // Password strength meter
    document.getElementById('rgPassword')?.addEventListener('input', (e) => {
        checkStrength(e.target.value);
    });

    // Nếu đã có token hợp lệ → redirect ngay
    const existingToken = localStorage.getItem(CONFIG.TOKEN_KEY);
    if (existingToken) {
        try {
            const p = decodeJwt(existingToken);
            if (p && p.exp * 1000 > Date.now()) {
                redirectByRole(existingToken);
                return;
            }
        } catch {}
        localStorage.removeItem(CONFIG.TOKEN_KEY);
    }
});
