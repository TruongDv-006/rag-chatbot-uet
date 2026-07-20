/**
 * ToastService.js – Hiển thị toast notification
 */
export class ToastService {
    constructor() {
        this.container = document.getElementById('toastContainer');
    }

    show(message, type = 'info', duration = 3500) {
        const icons = { success: 'fa-circle-check', error: 'fa-circle-xmark', info: 'fa-circle-info' };
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `<i class="fas ${icons[type] ?? icons.info}"></i><span>${message}</span>`;
        this.container.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('toast-out');
            toast.addEventListener('animationend', () => toast.remove());
        }, duration);
    }

    success(msg) { this.show(msg, 'success'); }
    error(msg)   { this.show(msg, 'error'); }
    info(msg)    { this.show(msg, 'info'); }
}
