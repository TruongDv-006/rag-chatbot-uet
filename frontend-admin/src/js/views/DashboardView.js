import ApiService from '../services/ApiService.js';
import TaskModel from '../models/TaskModel.js'; // 1. Nhập khẩu TaskModel vào đây

export default class DashboardView {
    constructor(appContainer) {
        this.appContainer = appContainer;
        this.taskModel = new TaskModel(); // 2. Tạo một cuốn sổ nhớ tác vụ riêng cho Dashboard
    }

    render() {
        this.appContainer.innerHTML = `
            <div class="card dashboard-card">
                <h1 style="margin-bottom: 20px;">Bảng Điều Khiển Hệ Thống RAG</h1>
                
                <div class="section">
                    <h3>1. Cập nhật dữ liệu Sổ tay (PDF/DOCX)</h3>
                    <p style="margin: 10px 0; color: #555;">Chọn file từ máy tính để hệ thống băm nhỏ và lưu vào Vector DB.</p>
                    
                    <input type="file" id="file-input" accept=".pdf, .docx">
                    <button id="upload-btn" class="btn" style="width: auto; padding: 10px 20px;">Tải lên & Tái Index</button>
                    
                    <p style="margin-top: 15px;">Trạng thái tải lên: <span id="upload-status" style="font-weight: bold;">Chưa chọn file</span></p>
                </div>

                <div class="section" style="background-color: #f9f9f9;">
                    <h3>2. Trạng thái Ingest (Background Worker)</h3>
                    <p style="margin-top: 10px;">Tiến trình hiện tại: <span id="ingest-status" class="text-warning">${this.taskModel.status}</span></p>
                </div>
            </div>
        `;
        this.bindEvents();
    }

    bindEvents() {
        const uploadBtn = document.getElementById('upload-btn');
        const fileInput = document.getElementById('file-input');
        const uploadStatus = document.getElementById('upload-status');

        uploadBtn.addEventListener('click', async () => {
            const file = fileInput.files[0];
            if (!file) {
                alert("Vui lòng chọn một file PDF hoặc DOCX trước!");
                return;
            }

            uploadStatus.innerText = "Đang tải file lên hệ thống...";

            const response = await ApiService.uploadFile(file);

            if (response.error) {
                uploadStatus.innerText = "Tải lên thất bại. Hãy kiểm tra Backend API.";
            } else {
                // 3. Khi Backend trả về task_id, lưu ngay vào Model
                this.taskModel.setTask(response.task_id); 
                
                uploadStatus.innerText = `Thành công! ID: ${this.taskModel.currentTaskId}`;
                document.getElementById('ingest-status').innerText = this.taskModel.status;
                
                this.startPollingStatus();
            }
        });
    }

    startPollingStatus() {
        const ingestStatus = document.getElementById('ingest-status');
        
        setInterval(async () => {
            const data = await ApiService.getIngestStatus();
            
            // 4. Mỗi lần hỏi thăm Backend xong, cập nhật kết quả vào Model trước
            this.taskModel.updateStatus(data.status || "Đang xử lý...");
            
            // 5. Rồi mới lấy dữ liệu từ Model vẽ lên màn hình
            ingestStatus.innerText = this.taskModel.status;
            
            if (this.taskModel.status === 'Hoàn thành') {
                ingestStatus.style.color = 'green';
            }
        }, 3000);
    }
}