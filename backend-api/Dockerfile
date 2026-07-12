# Sử dụng Python phiên bản 3.10 mượt mà cho AI
FROM python:3.10-slim

# Đặt thư mục làm việc bên trong container
WORKDIR /app

# Cài đặt các công cụ hệ thống cơ bản cần thiết nếu có build thư viện C++
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Lệnh chạy tạm thời để container không bị tắt (Vì bạn chưa có code)
# Khi nào viết xong code FastAPI, ta sẽ đổi lệnh này sau.
CMD ["python", "-c", "import time; import sys; print('Backend dang doi code Python...', flush=True); sys.stdout.flush(); [time.sleep(3600) for _ in range(24)]"]