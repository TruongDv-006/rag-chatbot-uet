export default class AdminModel {
    // Hàm constructor là nơi khởi tạo "trí nhớ" ban đầu khi vừa tải trang web
    constructor() {
        // Mặc định khi vừa vào web là chưa đăng nhập (false)
        this.isAuthenticated = false; 
        
        // Mặc định chưa có tên tài khoản
        this.username = null;
    }

    // Hành động 1: Ghi nhớ trạng thái khi đăng nhập thành công
    login(username) {
        this.isAuthenticated = true; // Đổi trạng thái thành "đã đăng nhập"
        this.username = username;    // Lưu lại tên người vừa đăng nhập
    }

    // Hành động 2: Xóa trí nhớ khi đăng xuất
    logout() {
        this.isAuthenticated = false; // Trả lại trạng thái "chưa đăng nhập"
        this.username = null;         // Xóa tên tài khoản
    }
}