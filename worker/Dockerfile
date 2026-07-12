FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Lệnh chạy tạm thời giữ container luôn sống để chờ bạn viết code Celery Worker
CMD ["python", "-c", "import time; import sys; print('Worker dang doi code xử lý dữ liệu...', flush=True); sys.stdout.flush(); [time.sleep(3600) for _ in range(24)]"]