events { worker_connections 1024; }

http {
    server {
        listen 80;

        # Mặc định trả về một câu chữ đơn giản khi thầy giáo vào cổng 80
        location / {
            return 200 'UET RAG System - He thong dang khoi tao ha tang Ngay 1 thanh cong!';
            add_header Content-Type text/plain;
        }
    }
}