export class ApiService {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl; // Địa chỉ chạy API của Backend
    }

    // Hàm gọi API POST /chat gửi kèm lịch sử cuộc trò chuyện
    async sendChat(historyPayload) {
        try {
            const response = await fetch(`${this.baseUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                // Biến đổi mảng dữ liệu lịch sử thành chuỗi JSON để truyền qua mạng
                body: JSON.stringify({ history: historyPayload })
            });

            if (!response.ok) {
                throw new Error(`Lỗi kết nối Backend! Mã lỗi: ${response.status}`);
            }

            // Trả về kết quả dạng JSON chứa { answer: "...", sources: [...] }
            return await response.json(); 
        } catch (error) {
            console.error("Lỗi tại ApiService:", error);
            throw error; // Đẩy lỗi ra ngoài để Controller xử lý hiển thị lỗi lên UI
        }
    }
}