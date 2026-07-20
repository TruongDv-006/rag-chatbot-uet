export class ChatView {
    constructor() {
        // Chủ động đi tìm các thẻ HTML bằng ID đã đặt ở Bước 1
        this.chatBox = document.getElementById('chatBox');
        this.userInput = document.getElementById('userInput');
        this.sendBtn = document.getElementById('sendBtn');
    }

    // Lấy nội dung chữ mà người dùng vừa gõ vào ô nhập liệu
    getInputValue() {
        return this.userInput.value.trim();
    }

    // Xóa sạch chữ trong ô nhập liệu sau khi bấm gửi để người dùng nhập câu tiếp theo
    clearInput() {
        this.userInput.value = '';
    }

    // Lắng nghe sự kiện khi người dùng nhấn nút Gửi hoặc gõ phím Enter
    bindSendMessage(handler) {
        this.sendBtn.addEventListener('click', handler);
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handler();
        });
    }

    // Đưa một tin nhắn bất kỳ lên màn hình hiển thị
    renderMessage(messageInstance) {
        const messageDiv = document.createElement('div');
        // Gán class để CSS tự động đẩy tin nhắn sang trái (bot) hoặc phải (user)
        messageDiv.className = `message ${messageInstance.role}-message`;

        let innerHTML = `<div class="bubble">${messageInstance.content}`;

        // ĐÂY CHÍNH LÀ MỤC TIÊU NGÀY 7: Hiển thị nguồn trích dẫn ngay dưới câu trả lời của Bot
        if (messageInstance.role === 'bot' && messageInstance.sources && messageInstance.sources.length > 0) {
            innerHTML += `<div class="sources-box">
                <strong>Nguồn trích dẫn:</strong>
                <ul style="margin-left: 20px; margin-top: 4px; padding-left: 0;">`;
            
            // Duyệt qua danh sách nguồn được Backend trả về để tạo các thẻ <li>
            messageInstance.sources.forEach(src => {
                innerHTML += `<li>📍 ${src.document_name} (Trang ${src.page})</li>`;
            });
            
            innerHTML += `</ul></div>`;
        }

        innerHTML += `</div>`;
        messageDiv.innerHTML = innerHTML;
        
        // Chèn thẻ tin nhắn mới này vào trong khung chat lớn
        this.chatBox.appendChild(messageDiv);
        this.scrollToBottom();
    }

    // Hiển thị trạng thái "Bot đang suy nghĩ..."
    showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message';
        loadingDiv.id = 'chat-loading';
        loadingDiv.innerHTML = `<div class="bubble"><em>🔍 Đang truy hồi sổ tay UET...</em></div>`;
        this.chatBox.appendChild(loadingDiv);
        this.scrollToBottom();
    }

    // Xóa dòng chữ trạng thái chờ sau khi Bot đã trả lời xong
    hideLoading() {
        const loadingElement = document.getElementById('chat-loading');
        if (loadingElement) loadingElement.remove();
    }

    // Luôn luôn tự động cuộn màn hình xuống dưới cùng để thấy tin nhắn mới nhất
    scrollToBottom() {
        this.chatBox.scrollTop = this.chatBox.scrollHeight;
    }
}