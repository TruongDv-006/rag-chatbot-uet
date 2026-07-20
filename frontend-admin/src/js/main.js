import AdminModel from './models/AdminModel.js';
import LoginView from './views/LoginView.js';
import DashboardView from './views/DashboardView.js';

class App {
    constructor() {
        // Lấy cái khung trống <div id="app"> từ index.html ra để chuẩn bị vẽ giao diện
        this.appContainer = document.getElementById('app');
        
        // Tạo mới một cuốn sổ tay quản lý bộ nhớ
        this.adminModel = new AdminModel();
        
        // Chạy ứng dụng ngay khi khởi tạo
        this.init();
    }

    // Hàm kiểm tra trạng thái để quyết định hiển thị màn hình nào
    init() {
        if (!this.adminModel.isAuthenticated) {
            this.showLogin();
        } else {
            this.showDashboard();
        }
    }

    // Hàm hiển thị màn hình Đăng nhập
    showLogin() {
        // Khởi tạo giao diện đăng nhập và truyền các linh kiện cần thiết vào
        const loginView = new LoginView(
            this.appContainer, 
            this.adminModel, 
            () => this.showDashboard() // Đây là hàm callback, khi đăng nhập đúng nó sẽ tự chạy showDashboard()
        );
        loginView.render();
    }

    // Hàm hiển thị màn hình Quản trị (Upload & Theo dõi Worker)
    showDashboard() {
        const dashboardView = new DashboardView(this.appContainer);
        dashboardView.render();
    }
}

// Lệnh dặn trình duyệt: "Chờ trang web index.html tải xong phần cứng thì kích hoạt bộ não App hoạt động"
document.addEventListener('DOMContentLoaded', () => {
    new App();
});