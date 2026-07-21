/**
 * main.js – AdminController: điều phối toàn bộ frontend-admin
 *
 * Luồng:
 *  1. Đọc JWT từ URL hash hoặc localStorage
 *  2. Kiểm tra isAuthenticated + isAdmin()
 *  3. Render dashboard, load dữ liệu trang Overview
 *  4. Điều hướng giữa các trang qua sidebar nav
 */
import { AuthService }  from './services/AuthService.js';
import { ApiService }   from './services/ApiService.js';
import { ToastService } from './services/ToastService.js';
import { AdminView }    from './views/AdminView.js';
import { CONFIG }       from './config.js';

class AdminController {
    constructor() {
        this.auth  = new AuthService();
        this.toast = new ToastService();
        this.view  = new AdminView();
        this.api   = new ApiService(this.auth);

        this._currentPage  = 'overview';
        this._allUsers     = [];
        this._pendingFiles = []; // Files chờ upload

        this._init();
    }

    /* ==========================================================
       KHỞI ĐỘNG
    ========================================================== */
    async _init() {
        this.auth.init();

        if (!this.auth.isAuthenticated()) {
            this.view.showAuthOverlay();
            document.getElementById('goToLoginBtn').href = `${CONFIG.LOGIN_PAGE_URL}/#logout=true`;
            return;
        }

        if (!this.auth.isAdmin()) {
            this.view.showAccessDenied();
            document.getElementById('backToUserBtn').href = CONFIG.USER_PAGE_URL;
            return;
        }

        this.view.showApp();
        this.view.setAdminInfo(this.auth.getUsername());
        this._bindEvents();

        await this._loadPage('overview');
        this.toast.success(`Chào mừng Admin ${this.auth.getUsername()}! 👑`);
    }

    /* ==========================================================
       BIND EVENTS
    ========================================================== */
    _bindEvents() {
        // Sidebar mobile
        document.getElementById('openSidebarBtn').addEventListener('click', () => this.view.openSidebar());
        document.getElementById('closeSidebarBtn').addEventListener('click', () => this.view.closeSidebar());
        document.getElementById('sidebarOverlay').addEventListener('click', () => this.view.closeSidebar());

        // Nav
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', async (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                if (page && page !== this._currentPage) {
                    this._currentPage = page;
                    this.view.setActivePage(page);
                    this.view.closeSidebar();
                    await this._loadPage(page);
                }
            });
        });

        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => this._loadPage(this._currentPage));

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => this._confirmLogout());

        // Upload modal
        document.getElementById('openUploadModalBtn').addEventListener('click', () => this.view.openUploadModal());
        document.getElementById('closeUploadModalBtn').addEventListener('click', () => this.view.closeUploadModal());
        document.getElementById('cancelUploadBtn').addEventListener('click', () => this.view.closeUploadModal());
        document.getElementById('startUploadBtn').addEventListener('click', () => this._startUpload());

        // File input via browse button
        this.view.fileInput.addEventListener('change', (e) => this._addFilesToQueue([...e.target.files]));

        // Drag & Drop for modal dropzone
        this._setupDropZone(this.view.dropZone, (files) => this._addFilesToQueue(files));

        // Mini drop zone (overview)
        this.view.miniFileInput.addEventListener('change', (e) => this._quickUpload([...e.target.files]));
        this._setupDropZone(this.view.miniDropZone, (files) => this._quickUpload(files));

        // Doc search
        document.getElementById('docSearchInput')?.addEventListener('input', () => this._filterDocTable());

        // User search + filter
        document.getElementById('userSearchInput')?.addEventListener('input', () => this._filterUserTable());
        document.getElementById('roleFilter')?.addEventListener('change', () => this._filterUserTable());

        // Refresh tasks
        document.getElementById('refreshTasksBtn')?.addEventListener('click', () => this._loadTasks());
    }

    /* ==========================================================
       PAGE LOADING
    ========================================================== */
    async _loadPage(page) {
        switch (page) {
            case 'overview':  await this._loadOverview();  break;
            case 'documents': await this._loadDocuments(); break;
            case 'users':     await this._loadUsers();     break;
            case 'tasks':     await this._loadTasks();     break;
        }
    }

    async _loadOverview() {
        try {
            const stats = await this.api.getStats();
            this.view.renderStats(stats);
            if (stats.recent_activity) this.view.renderActivity(stats.recent_activity);
        } catch (err) {
            this._handleApiError(err, 'Không tải được thống kê', /* showFallback */ true);
        }
    }

    async _loadDocuments() {
        this.view.docsTableBody.innerHTML = `<tr><td colspan="7" class="table-loading"><i class="fas fa-spinner fa-spin"></i> Đang tải...</td></tr>`;
        try {
            const docs = await this.api.getDocuments();
            this._cachedDocs = docs;
            this.view.renderDocuments(docs, (id, name) => this._deleteDocument(id, name));
        } catch (err) {
            this._handleApiError(err, 'Không tải được danh sách tài liệu');
            this.view.docsTableBody.innerHTML = `<tr><td colspan="7" class="table-loading">Không thể tải dữ liệu.</td></tr>`;
        }
    }

    _filterDocTable() {
        const q = document.getElementById('docSearchInput')?.value ?? '';
        const filtered = (this._cachedDocs ?? []).filter(d =>
            (d.filename ?? d.name ?? '').toLowerCase().includes(q.toLowerCase())
        );
        this.view.renderDocuments(filtered, (id, name) => this._deleteDocument(id, name));
    }

    async _loadUsers() {
        this.view.usersTableBody.innerHTML = `<tr><td colspan="7" class="table-loading"><i class="fas fa-spinner fa-spin"></i> Đang tải...</td></tr>`;
        try {
            this._allUsers = await this.api.getUsers();
            this.view.renderUsers(this._allUsers);
        } catch (err) {
            this._handleApiError(err, 'Không tải được danh sách người dùng');
            this.view.usersTableBody.innerHTML = `<tr><td colspan="7" class="table-loading">Không thể tải dữ liệu.</td></tr>`;
        }
    }

    _filterUserTable() {
        const q    = document.getElementById('userSearchInput')?.value ?? '';
        const role = document.getElementById('roleFilter')?.value ?? '';
        this.view.renderUsers(this._allUsers, q, role);
    }

    async _loadTasks() {
        this.view.tasksList.innerHTML = `<div class="table-loading"><i class="fas fa-spinner fa-spin"></i> Đang tải...</div>`;
        try {
            const tasks = await this.api.getTasks();
            this.view.renderTasks(tasks);
        } catch (err) {
            this._handleApiError(err, 'Không tải được danh sách tasks');
            this.view.tasksList.innerHTML = `<div class="table-loading">Không thể kết nối đến Worker.</div>`;
        }
    }

    /* ==========================================================
       UPLOAD DOCUMENT
    ========================================================== */
    _addFilesToQueue(files) {
        const valid = files.filter(f => f.type === 'application/pdf' || f.name.endsWith('.docx'));
        if (valid.length < files.length) this.toast.error('Chỉ chấp nhận file PDF hoặc DOCX.');

        valid.forEach(file => {
            if (this._pendingFiles.some(f => f.file.name === file.name)) return;
            const item = this.view.addFileToQueue(file);
            // Remove button
            item.querySelector('.file-remove').addEventListener('click', () => {
                this._pendingFiles = this._pendingFiles.filter(f => f.file.name !== file.name);
                item.remove();
                this.view.setStartUploadEnabled(this._pendingFiles.length > 0);
            });
            this._pendingFiles.push({ file, item });
        });

        this.view.setStartUploadEnabled(this._pendingFiles.length > 0);
    }

    async _startUpload() {
        if (!this._pendingFiles.length) return;
        document.getElementById('startUploadBtn').disabled = true;

        let successCount = 0;
        for (const { file, item } of this._pendingFiles) {
            try {
                await this.api.uploadDocument(file, (pct) => this.view.updateFileProgress(item, pct));
                this.view.setFileSuccess(item);
                successCount++;
            } catch (err) {
                this.view.setFileError(item, err.message);
                this.toast.error(`Lỗi upload "${file.name}": ${err.message}`);
            }
        }

        this._pendingFiles = [];
        if (successCount > 0) {
            this.toast.success(`Đã tải lên thành công ${successCount} tài liệu!`);
            setTimeout(() => {
                this.view.closeUploadModal();
                if (this._currentPage === 'documents') this._loadDocuments();
                if (this._currentPage === 'overview')  this._loadOverview();
            }, 1800);
        }
    }

    /** Quick upload từ overview panel */
    async _quickUpload(files) {
        const valid = files.filter(f => f.type === 'application/pdf' || f.name.endsWith('.docx'));
        if (!valid.length) { this.toast.error('Chỉ chấp nhận file PDF hoặc DOCX.'); return; }

        this.view.miniUploadStatus.innerHTML = `<div style="margin-top:10px;font-size:.82rem;color:var(--text-secondary);">
            <i class="fas fa-spinner fa-spin"></i> Đang tải lên ${valid.length} file...
        </div>`;

        let ok = 0;
        for (const f of valid) {
            try { await this.api.uploadDocument(f, () => {}); ok++; }
            catch (e) { this.toast.error(`Lỗi: ${e.message}`); }
        }

        this.view.miniUploadStatus.innerHTML = ok > 0
            ? `<div style="margin-top:10px;font-size:.82rem;color:var(--green);"><i class="fas fa-circle-check"></i> Đã tải lên ${ok} tài liệu thành công!</div>`
            : '';

        if (ok > 0) { this.toast.success(`Tải lên ${ok} tài liệu thành công!`); this._loadOverview(); }
    }

    /* ==========================================================
       DELETE DOCUMENT
    ========================================================== */
    async _deleteDocument(docId, docName) {
        const ok = await this.view.showConfirm(
            'Xoá tài liệu',
            `Bạn có chắc muốn xóa tài liệu "${docName}"? Dữ liệu vector sẽ bị xoá khỏi Qdrant.`
        );
        if (!ok) return;
        try {
            await this.api.deleteDocument(docName);
            this.toast.success(`Đã xóa tài liệu "${docName}"`);
            this._loadDocuments();
        } catch (err) {
            this.toast.error(`Xóa thất bại: ${err.message}`);
        }
    }

    /* ==========================================================
       LOGOUT
    ========================================================== */
    async _confirmLogout() {
        const ok = await this.view.showConfirm('Đăng xuất', 'Bạn có muốn đăng xuất không?');
        if (ok) {
            this.auth.clearToken();
            this.auth.redirectToLogin();
        }
    }

    /* ==========================================================
       DRAG & DROP SETUP
    ========================================================== */
    _setupDropZone(el, onFiles) {
        el.addEventListener('dragover',  (e) => { e.preventDefault(); el.classList.add('dragover'); });
        el.addEventListener('dragleave', ()  => el.classList.remove('dragover'));
        el.addEventListener('drop',      (e) => {
            e.preventDefault(); el.classList.remove('dragover');
            onFiles([...e.dataTransfer.files]);
        });
    }

    /* ==========================================================
       ERROR HANDLING
    ========================================================== */
    _handleApiError(err, fallbackMsg, showFallbackStats = false) {
        console.error(err);
        this.toast.error(fallbackMsg);
        if (showFallbackStats) {
            this.view.renderStats({ total_users: '–', total_documents: '–', total_sessions: '–', pending_tasks: '0' });
            this.view.renderActivity([]);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => { new AdminController(); });