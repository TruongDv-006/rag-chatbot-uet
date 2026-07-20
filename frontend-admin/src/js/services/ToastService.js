/**
 * ToastService.js
 */
export class ToastService {
    constructor() { this.el = document.getElementById('toastContainer'); }
    show(msg, type='info', ms=3500) {
        const icons = { success:'fa-circle-check', error:'fa-circle-xmark', info:'fa-circle-info' };
        const t = document.createElement('div');
        t.className = `toast toast-${type}`;
        t.innerHTML = `<i class="fas ${icons[type]||icons.info}"></i><span>${msg}</span>`;
        this.el.appendChild(t);
        setTimeout(() => { t.classList.add('toast-out'); t.addEventListener('animationend', ()=>t.remove()); }, ms);
    }
    success(m){ this.show(m,'success'); }
    error(m)  { this.show(m,'error'); }
    info(m)   { this.show(m,'info'); }
}
