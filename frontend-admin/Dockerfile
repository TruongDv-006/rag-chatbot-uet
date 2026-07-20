# Sử dụng image Nginx bản ổn định và nhẹ (Alpine Linux) giống frontend-user
FROM nginx:1.25-alpine

# Thao tác xóa sạch các cấu hình và file mặc định của Nginx để tránh xung đột
RUN rm -rf /usr/share/nginx/html/*

# Bản chất code Vanilla JS của bạn đang nằm trực tiếp ở thư mục hiện tại
# Copy toàn bộ file tĩnh (index.html, css/, js/) vào thư mục phục vụ của Nginx
COPY . /usr/share/nginx/html

# Expose port 80 - cổng chạy mặc định của web server Nginx bên trong container
EXPOSE 80

# Khởi chạy Nginx ở chế độ background giữ container luôn sống và sẵn sàng phục vụ
CMD ["nginx", "-g", "daemon off;"]