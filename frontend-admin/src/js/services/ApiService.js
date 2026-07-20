export default class ApiService {
    
    // Nhiệm vụ 1: Mang tài khoản, mật khẩu đi hỏi Backend xem có đúng không
    static async authenticate(username, password) {
        // Tạm thời ở bước này, mình giả lập việc chờ đợi mạng mất 0.5 giây (500ms)
        // Nếu gõ đúng 'admin' và 'uet123' thì trả về true (thành công)
        return new Promise((resolve) => {
            setTimeout(() => {
                if (username === 'admin' && password === 'uet123') {
                    resolve(true);
                } else {
                    resolve(false);
                }
            }, 500);
        });
    }

    // Nhiệm vụ 2: Đóng gói file PDF/DOCX và gửi lên cổng /api/upload
    static async uploadFile(file) {
        // Trình duyệt dùng một cái "hộp" tên là FormData để đóng gói file chứa dung lượng lớn
        const formData = new FormData();
        formData.append('file', file);

        try {
            // Dùng lệnh 'fetch' để ném cái hộp đó sang cho Backend
            const response = await fetch('/api/upload', { 
                method: 'POST', 
                body: formData 
            });
            // Lấy câu trả lời từ Backend (dưới dạng JSON) mang về
            return await response.json(); 
        } catch (error) {
            console.error("Lỗi khi gửi file:", error);
            return { error: true };
        }
    }

    // Nhiệm vụ 3: Hỏi thăm Backend xem hệ thống (Worker) đã băm file xong chưa
    static async getIngestStatus() {
        try {
            const response = await fetch('/api/status');
            return await response.json();
        } catch (error) {
            return { status: 'Lỗi kết nối Backend' };
        }
    }
}