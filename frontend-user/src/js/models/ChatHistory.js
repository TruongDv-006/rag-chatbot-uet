export class ChatHistory {
    constructor() {
        this.messages = []; // Ban đầu khởi tạo một mảng rỗng để chứa các tin nhắn
    }

    // Hàm dùng để thêm một tin nhắn mới vào trong danh sách lịch sử
    addMessage(messageInstance) {
        this.messages.push(messageInstance);
    }

    // Hàm cực kỳ quan trọng: Lấy toàn bộ các tin nhắn đã có, 
    // duyệt qua từng tin và biến đổi nó thành định dạng chuẩn để sẵn sàng gửi lên Backend API
    getHistoryForApi() {
        return this.messages.map(msg => msg.toApiFormat());
    }

    // Hàm dùng để xóa sạch lịch sử chat nếu người dùng muốn làm mới cuộc hội thoại
    clear() {
        this.messages = [];
    }
}