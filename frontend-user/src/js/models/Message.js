export class Message {
    // Hàm khởi tạo: Khi tạo một tin nhắn, ta cần truyền vào người gửi (role), nội dung (content) và nguồn (sources)
    constructor(role, content, sources = []) {
        this.role = role;       // Chỉ nhận giá trị 'user' (người dùng) hoặc 'bot' (chatbot)
        this.content = content; // Chuỗi chữ nội dung tin nhắn
        this.sources = sources; // Mảng chứa danh sách các nguồn trích dẫn [{document_name, page}]
    }

    // Hàm này giúp chuyển đổi tin nhắn thành định dạng chuẩn mà Backend yêu cầu
    // Backend chỉ cần biết role và content, không cần biết các thông tin dư thừa khác
    toApiFormat() {
        return {
            role: this.role,
            content: this.content
        };
    }
}