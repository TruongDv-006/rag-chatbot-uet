FROM python:3.10-slim

WORKDIR /app

# Cài đặt các công cụ hệ thống (curl, lõi OCR Tesseract Tiếng Việt và Poppler chuyển PDF thành ảnh)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    tesseract-ocr-vie \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements vào trước để tận dụng cơ chế đóng gói cache của Docker
COPY requirements.txt .

# Tiến hành cài đặt các thư viện Python (bao gồm pytesseract, pdf2image, Pillow từ requirements)
RUN pip install --no-cache-dir -r requirements.txt

# Lệnh chạy tạm thời giữ container luôn sống để chờ bạn viết code Celery Worker
CMD ["python", "-c", "import time; import sys; print('Worker dang doi code xử lý dữ liệu...', flush=True); sys.stdout.flush(); [time.sleep(3600) for _ in range(24)]"]