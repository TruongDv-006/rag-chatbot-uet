export default class TaskModel {
    constructor() {
        this.currentTaskId = null;     // Ghi nhớ ID của file đang được đưa vào Queue
        this.status = 'Chưa có tác vụ'; // Ghi nhớ trạng thái: 'Đang xử lý' hoặc 'Hoàn thành'
    }

    // Hành động 1: Khi Backend nhận file và cấp cho một cái Task ID
    setTask(taskId) {
        this.currentTaskId = taskId;
        this.status = 'Đang xử lý (Chunking & Embedding)...';
    }

    // Hành động 2: Cập nhật trạng thái mới nhận từ Worker về
    updateStatus(newStatus) {
        this.status = newStatus;
    }
}