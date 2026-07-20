import ApiService from '../services/ApiService.js';

export default class LoginView {
    // Bây giờ constructor nhận thêm: adminModel (để lưu trạng thái) và onLoginSuccess (để báo cho file Main biết khi nào cần chuyển trang)
    constructor(appContainer, adminModel, onLoginSuccess) {
        this.appContainer = appContainer;
        this.adminModel = adminModel;
        this.onLoginSuccess = onLoginSuccess;
    }

    render() {
        this.appContainer.innerHTML = `
            <div class="card login-card">
                <h2 style="text-align: center; margin-bottom: 20px;">Đăng nhập Admin Panel</h2>
                <p id="error-msg" class="text-error"></p>
                
                <form id="login-form">
                    <label>Tài khoản:</label>
                    <input type="text" id="username" placeholder="Nhập admin..." required>
                    
                    <label>Mật khẩu:</label>
                    <input type="password" id="password" placeholder="Nhập mật khẩu..." required>
                    
                    <button type="submit" class="btn">Đăng nhập</button>
                </form>
            </div>
        `;
        // Vẽ xong giao diện thì phải kích hoạt chức năng lắng nghe nút bấm ngay lập tức
        this.bindEvents();
    }

    // Hàm lắng nghe sự kiện gõ chữ và ấn nút
    bindEvents() {
        const form = document.getElementById('login-form');
        const errorMsg = document.getElementById('error-msg');

        form.addEventListener('submit', async (e) => {
            e.preventDefault(); // Ngăn trang web bị tải lại (F5) vô lý khi ấn nút
            
            const user = document.getElementById('username').value;
            const pass = document.getElementById('password').value;

            errorMsg.innerText = "Đang kiểm tra...";

            // Gọi người đưa thư (Service) đi hỏi Backend
            const isValid = await ApiService.authenticate(user, pass);

            if (isValid) {
                this.adminModel.login(user); // Đăng nhập đúng -> Cập nhật vào Bộ nhớ (Model)
                this.onLoginSuccess();       // Báo hiệu chuyển sang trang Dashboard
            } else {
                errorMsg.innerText = "Sai tài khoản hoặc mật khẩu!"; // Đăng nhập sai -> Báo lỗi lên màn hình
            }
        });
    }
}