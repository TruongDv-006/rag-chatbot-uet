// 1. Nhập (Import) tất cả các linh kiện từ các file khác vào đây
import { ChatHistory } from './models/ChatHistory.js';
import { Message } from './models/Message.js';
import { ApiService } from './services/ApiService.js';
import { ChatView } from './views/ChatView.js';

// 2. Định nghĩa lớp AppController để điều khiển toàn bộ ứng dụng
class AppController {
    constructor() {
        // Khởi tạo các đối tượng độc lập từ các Class đã viết
        this.history = new ChatHistory();
        this.view = new ChatView();
        
        // Cấu hình URL của Backend API. 
        // Sau này khi chạy Docker Compose qua Nginx, bạn có thể sửa thành '/api' hoặc giữ nguyên port 8000
        this.api = new ApiService('http://localhost:8000'); 

        // Ra lệnh cho Giao diện (View) nghe ngóng: Khi nào người dùng bấm nút gửi hoặc nhấn Enter,
        // thì lập tức gọi hàm `handleUserAction` để xử lý.
        this.view.bindSendMessage(this.handleUserAction.bind(this));
    }

    // 3. Kịch bản xử lý dòng chảy dữ liệu khi người dùng gửi câu hỏi
    async handleUserAction() {
        // Lấy chữ người dùng vừa nhập
        const text = this.view.getInputValue();
        if (!text) return; // Nếu ô nhập rỗng thì không làm gì cả

        // --- BƯỚC A: XỬ LÝ PHÍA NGƯỜI DÙNG ---
        // Tạo một đối tượng Tin nhắn mới của Người dùng
        const userMessage = new Message('user', text);
        // Thêm câu hỏi này vào cuốn sổ lịch sử để lưu ngữ cảnh đa lượt
        this.history.addMessage(userMessage);
        // Ra lệnh cho Giao diện hiển thị tin nhắn này lên màn hình bên phải
        this.view.renderMessage(userMessage);
        // Xóa sạch ô nhập liệu để người dùng sẵn sàng gõ câu tiếp theo
        this.view.clearInput();

        // --- BƯỚC B: CHỜ ĐỢI BACKEND ---
        // Bật dòng chữ hiệu ứng "🔍 Đang truy hồi sổ tay UET..."
        this.view.showLoading();

        try {
            // --- BƯỚC C: GỌI API TRUY HỒI ĐA LƯỢT (MỤC TIÊU NGÀY 7) ---
            // Lấy toàn bộ mảng lịch sử từ trước đến nay đã được format đúng chuẩn
            const payload = this.history.getHistoryForApi();
            // Bắn dữ liệu lên Backend API và chờ kết quả trả về
            const responseData = await this.api.sendChat(payload);

            // --- BƯỚC D: XỬ LÝ PHÍA BOT ---
            // Tạo một đối tượng Tin nhắn mới cho Bot (Có kèm câu trả lời và mảng Nguồn trích dẫn)
            const botMessage = new Message('bot', responseData.answer, responseData.sources);
            // Lưu câu trả lời của Bot vào lịch sử để làm ngữ cảnh cho các câu hỏi tiếp theo
            this.history.addMessage(botMessage);

            // Tắt dòng chữ hiệu ứng chờ đợi đi
            this.view.hideLoading();
            // Ra lệnh cho Giao diện vẽ câu trả lời của Bot kèm Nguồn trích dẫn lên màn hình bên trái
            this.view.renderMessage(botMessage);

        } catch (error) {
            // Nếu có lỗi mạng hoặc Backend sập, tắt hiệu ứng chờ và báo lỗi cho người dùng biết
            this.view.hideLoading();
            const errorMessage = new Message('bot', 'Đã xảy ra lỗi kết nối với hệ thống RAG Microservices. Bạn hãy kiểm tra lại Backend nhé!');
            this.view.renderMessage(errorMessage);
        }
    }
}

// 4. Lệnh kích hoạt: Chờ trang web hiển thị hoàn toàn trên trình duyệt thì khởi chạy hệ thống
document.addEventListener('DOMContentLoaded', () => {
    new AppController();
});