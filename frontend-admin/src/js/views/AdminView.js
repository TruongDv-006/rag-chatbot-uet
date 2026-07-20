/**
 * AdminView.js – Toàn bộ DOM rendering cho Admin Dashboard
 */
export class AdminView {
    constructor() {
        // Overlays
        this.authOverlay        = document.getElementById('authOverlay');
        this.accessDeniedOverlay= document.getElementById('accessDeniedOverlay');
        this.adminLayout        = document.getElementById('adminLayout');

        // Sidebar
        this.sidebar        = document.getElementById('sidebar');
        this.sidebarOverlay = document.getElementById('sidebarOverlay');
        this.adminAvatar    = document.getElementById('adminAvatar');
        this.adminName      = document.getElementById('adminName');

        // Topbar
        this.topbarIcon = document.getElementById('topbarIcon');
        this.topbarText = document.getElementById('topbarText');
        this.topbarTime = document.getElementById('topbarTime');

        // Pages
        this.pages = {
            overview:  document.getElementById('page-overview'),
            documents: document.getElementById('page-documents'),
            users:     document.getElementById('page-users'),
            tasks:     document.getElementById('page-tasks'),
        };

        // Stats
        this.statTotalUsers    = document.getElementById('statTotalUsers');
        this.statTotalDocs     = document.getElementById('statTotalDocs');
        this.statTotalSessions = document.getElementById('statTotalSessions');
        this.statPendingTasks  = document.getElementById('statPendingTasks');
        this.recentActivity    = document.getElementById('recentActivity');

        // Tables
        this.docsTableBody  = document.getElementById('docsTableBody');
        this.usersTableBody = document.getElementById('usersTableBody');
        this.tasksList      = document.getElementById('tasksList');
        this.taskBadge      = document.getElementById('taskBadge');
        this.userCountPill  = document.getElementById('userCountPill');

        // Upload Modal
        this.uploadModal      = document.getElementById('uploadModal');
        this.dropZone         = document.getElementById('dropZone');
        this.fileInput        = document.getElementById('fileInput');
        this.fileQueue        = document.getElementById('fileQueue');
        this.startUploadBtn   = document.getElementById('startUploadBtn');

        // Mini drop zone (overview)
        this.miniDropZone   = document.getElementById('miniDropZone');
        this.miniFileInput  = document.getElementById('miniFileInput');
        this.miniUploadStatus = document.getElementById('miniUploadStatus');

        // Confirm modal
        this.confirmModal    = document.getElementById('confirmModal');
        this.confirmTitle    = document.getElementById('confirmTitle');
        this.confirmDesc     = document.getElementById('confirmDesc');
        this.confirmOkBtn    = document.getElementById('confirmOkBtn');
        this.confirmCancelBtn= document.getElementById('confirmCancelBtn');

        this._startClock();
    }

    /* ======= AUTH SCREENS ======= */
    showAuthOverlay()        { this.authOverlay.classList.remove('hidden'); }
    showAccessDenied()       { this.accessDeniedOverlay.classList.remove('hidden'); }
    showApp() {
        this.authOverlay.classList.add('hidden');
        this.accessDeniedOverlay.classList.add('hidden');
        this.adminLayout.classList.remove('hidden');
    }

    setAdminInfo(username) {
        this.adminName.textContent = username;
        this.adminAvatar.textContent = username.charAt(0).toUpperCase();
    }

    /* ======= SIDEBAR ======= */
    openSidebar()  { this.sidebar.classList.add('open'); this.sidebarOverlay.classList.add('show'); }
    closeSidebar() { this.sidebar.classList.remove('open'); this.sidebarOverlay.classList.remove('show'); }

    setActivePage(pageKey) {
        const labels = {
            overview:  { icon:'fa-chart-pie',  text:'Tổng quan hệ thống' },
            documents: { icon:'fa-file-pdf',   text:'Quản lý tài liệu' },
            users:     { icon:'fa-users',       text:'Quản lý người dùng' },
            tasks:     { icon:'fa-gears',       text:'Hàng đợi Worker' },
        };
        // Pages
        Object.entries(this.pages).forEach(([k, el]) => el.classList.toggle('hidden', k !== pageKey));
        // Nav highlights
        document.querySelectorAll('.nav-item').forEach(item => item.classList.toggle('active', item.dataset.page === pageKey));
        // Topbar
        const lbl = labels[pageKey] || labels.overview;
        this.topbarIcon.className = `fas ${lbl.icon}`;
        this.topbarText.textContent = lbl.text;
    }

    /* ======= STATS ======= */
    renderStats(data) {
        this.statTotalUsers.textContent    = data.total_users    ?? '–';
        this.statTotalDocs.textContent     = data.total_documents ?? '–';
        this.statTotalSessions.textContent = data.total_sessions  ?? '–';
        this.statPendingTasks.textContent  = data.pending_tasks   ?? '0';
    }

    renderActivity(activities) {
        if (!activities?.length) {
            this.recentActivity.innerHTML = `<p style="color:var(--text-muted);font-size:.84rem;">Chưa có hoạt động nào.</p>`;
            return;
        }
        this.recentActivity.innerHTML = activities.map(a => `
            <div class="activity-item">
                <div class="activity-dot ${a.type ?? ''}"></div>
                <div class="activity-text">
                    <strong>${this._esc(a.actor ?? '')}</strong> ${this._esc(a.action ?? '')}
                    <div class="activity-time">${this._fmtDate(a.time)}</div>
                </div>
            </div>`).join('');
    }

    /* ======= DOCUMENTS TABLE ======= */
    renderDocuments(docs, onDelete) {
        if (!docs?.length) {
            this.docsTableBody.innerHTML = `<tr><td colspan="7" class="table-loading">Chưa có tài liệu nào.</td></tr>`;
            return;
        }
        this.docsTableBody.innerHTML = docs.map((d, i) => `
            <tr>
                <td>${i + 1}</td>
                <td class="td-name"><i class="fas fa-file-pdf" style="color:var(--red);margin-right:8px;"></i>${this._esc(d.filename ?? d.name)}</td>
                <td><span class="badge badge-info">${(d.file_type ?? 'PDF').toUpperCase()}</span></td>
                <td>${this._fmtSize(d.file_size ?? d.size)}</td>
                <td>${this._statusBadge(d.status)}</td>
                <td>${this._fmtDate(d.created_at ?? d.uploaded_at)}</td>
                <td>
                    <button class="tbl-btn danger delete-doc-btn" data-id="${d.id}" data-name="${this._esc(d.filename ?? d.name)}">
                        <i class="fas fa-trash-can"></i> Xóa
                    </button>
                </td>
            </tr>`).join('');

        this.docsTableBody.querySelectorAll('.delete-doc-btn').forEach(btn => {
            btn.addEventListener('click', () => onDelete(btn.dataset.id, btn.dataset.name));
        });
    }

    /* ======= USERS TABLE ======= */
    renderUsers(users, filterText='', filterRole='') {
        let list = users ?? [];
        if (filterText) list = list.filter(u => (u.username+u.email+u.full_name).toLowerCase().includes(filterText.toLowerCase()));
        if (filterRole) list = list.filter(u => u.role === filterRole);

        this.userCountPill.textContent = list.length;

        if (!list.length) {
            this.usersTableBody.innerHTML = `<tr><td colspan="7" class="table-loading">Không tìm thấy người dùng nào.</td></tr>`;
            return;
        }
        this.usersTableBody.innerHTML = list.map((u, i) => `
            <tr>
                <td>${i + 1}</td>
                <td>
                    <div class="td-avatar">
                        <div class="td-avatar-icon">${(u.username ?? u.full_name ?? '?').charAt(0).toUpperCase()}</div>
                        <div>
                            <div class="td-name">${this._esc(u.full_name ?? u.username)}</div>
                            <div style="font-size:.72rem;color:var(--text-muted);">@${this._esc(u.username)}</div>
                        </div>
                    </div>
                </td>
                <td>${this._esc(u.email ?? '–')}</td>
                <td>${this._roleBadge(u.role)}</td>
                <td>${this._fmtDate(u.created_at)}</td>
                <td>${u.session_count ?? '–'}</td>
                <td>
                    <button class="tbl-btn"><i class="fas fa-eye"></i> Chi tiết</button>
                </td>
            </tr>`).join('');
    }

    /* ======= TASKS ======= */
    renderTasks(tasks) {
        const pending = (tasks ?? []).filter(t => t.status === 'PENDING' || t.status === 'STARTED').length;
        this.taskBadge.textContent = pending;
        this.taskBadge.style.display = pending > 0 ? '' : 'none';

        if (!tasks?.length) {
            this.tasksList.innerHTML = `<div class="table-loading">Không có task nào trong hàng đợi.</div>`;
            return;
        }
        this.tasksList.innerHTML = tasks.map(t => {
            const colors = { SUCCESS:'green', FAILURE:'red', PENDING:'orange', STARTED:'blue' };
            const c = colors[t.status] ?? 'blue';
            return `
            <div class="task-card">
                <div class="task-card-icon" style="background:var(--${c}-bg);color:var(--${c});">
                    <i class="fas ${t.status==='SUCCESS'?'fa-circle-check':t.status==='FAILURE'?'fa-circle-xmark':'fa-rotate-right fa-spin'}"></i>
                </div>
                <div class="task-body">
                    <div class="task-name">${this._esc(t.filename ?? t.args?.[0] ?? 'Task không xác định')}</div>
                    <div class="task-meta">Khởi tạo: ${this._fmtDate(t.created_at)} &nbsp;|&nbsp; Worker: ${this._esc(t.worker ?? 'uet_worker')}</div>
                    <div class="task-id">ID: ${this._esc(t.task_id ?? t.id)}</div>
                </div>
                <span class="badge badge-${c==='green'?'success':c==='red'?'error':c==='orange'?'warning':'info'}">
                    ${this._esc(t.status)}
                </span>
            </div>`;
        }).join('');
    }

    /* ======= UPLOAD MODAL ======= */
    openUploadModal()  { this.uploadModal.classList.remove('hidden'); }
    closeUploadModal() { this.uploadModal.classList.add('hidden'); this.clearFileQueue(); }

    /** Thêm file vào queue UI, trả về item element để cập nhật progress */
    addFileToQueue(file) {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.dataset.name = file.name;
        item.innerHTML = `
            <i class="fas fa-file-pdf file-icon"></i>
            <div class="file-info">
                <div class="file-name">${this._esc(file.name)}</div>
                <div class="file-size">${this._fmtSize(file.size)}</div>
                <div class="file-progress"><div class="file-progress-bar" style="width:0%"></div></div>
            </div>
            <span class="file-status-icon" style="color:var(--text-muted);"><i class="fas fa-clock"></i></span>
            <i class="fas fa-times file-remove"></i>`;
        this.fileQueue.appendChild(item);
        return item;
    }

    updateFileProgress(item, pct) {
        item.querySelector('.file-progress-bar').style.width = pct + '%';
    }

    setFileSuccess(item) {
        item.querySelector('.file-status-icon').innerHTML = `<i class="fas fa-circle-check" style="color:var(--green)"></i>`;
        item.querySelector('.file-remove').style.display = 'none';
    }

    setFileError(item, msg) {
        item.querySelector('.file-status-icon').innerHTML = `<i class="fas fa-circle-xmark" style="color:var(--red)" title="${this._esc(msg)}"></i>`;
    }

    clearFileQueue()          { this.fileQueue.innerHTML = ''; }
    setStartUploadEnabled(en) { this.startUploadBtn.disabled = !en; }

    /* ======= CONFIRM MODAL ======= */
    showConfirm(title, desc) {
        return new Promise(resolve => {
            this.confirmTitle.textContent = title;
            this.confirmDesc.textContent  = desc;
            this.confirmModal.classList.remove('hidden');
            const close = (r) => { this.confirmModal.classList.add('hidden'); resolve(r); };
            this.confirmOkBtn.onclick     = () => close(true);
            this.confirmCancelBtn.onclick = () => close(false);
        });
    }

    /* ======= PRIVATE ======= */
    _startClock() {
        const tick = () => {
            this.topbarTime.textContent = new Date().toLocaleTimeString('vi-VN', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
        };
        tick();
        setInterval(tick, 1000);
    }

    _esc(s) {
        return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    _fmtDate(d) {
        if (!d) return '–';
        try { return new Date(d).toLocaleDateString('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'}); }
        catch { return String(d); }
    }

    _fmtSize(bytes) {
        if (!bytes) return '–';
        const b = Number(bytes);
        if (b >= 1024*1024) return (b/1024/1024).toFixed(1) + ' MB';
        if (b >= 1024) return (b/1024).toFixed(0) + ' KB';
        return b + ' B';
    }

    _statusBadge(status) {
        const map = {
            processed: ['success','Đã xử lý'], pending: ['warning','Đang xử lý'],
            failed: ['error','Lỗi'], indexed: ['success','Đã index'], uploaded: ['info','Đã tải lên'],
        };
        const [cls, label] = map[status] ?? ['info', status ?? 'Không rõ'];
        return `<span class="badge badge-${cls}">${label}</span>`;
    }

    _roleBadge(role) {
        return role === 'admin'
            ? `<span class="badge badge-purple"><i class="fas fa-crown"></i> Admin</span>`
            : `<span class="badge badge-info"><i class="fas fa-user-graduate"></i> Student</span>`;
    }
}
