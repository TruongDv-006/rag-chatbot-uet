from fastapi import HTTPException, status
from sqlalchemy.orm import Session # pyrefly:ignore
from app.models.user import User # pyrefly: ignore 
from app.untils.security import get_password_hash, verify_password, create_access_token # pyrefly: ignore


class AuthService:
    """Nơi xử lý Đăng ký/ Đăng nhập"""
    def register_student (self, db:Session, user_data:dict):
        """ Xử lý logic cho sinh viên đăng ký tài khoản mới
        Các tham số đầu vào:
        - db: Session là một đường ống kết nối xuống PostgreSQL.
              Nhờ có tham số này AuthService có khả năng dùng: db.query(),db.commit()...
        - user_data: dict: Thông tin mà Frontend gửi qua Router có dạng
            {"username": "truongdv", "email": "...", "full_name": "...", "password": "..."}
        """
        # Kiểm tra xem có ai dùng tên đăng nhập hoặc email này chưa
        existing_username = db.query(User).filter(User.username == user_data["username"]).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tên đăng nhập này đã tồn tại trên hệ thống. Vui lòng nhập Tên đăng nhập khác"
            )
        existing_email = db.query(User).filter(User.email == user_data["email"]).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email này đã tồn tại trên hệ thống. Vui lòng nhập Email khác"
            )
        # Băm mật khẩu thô trước khi lưu vào db
        hashed_pwd = get_password_hash(user_data["password"])

        # Tạo ra dối tượng để lưu 
        new_user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password = hashed_pwd,
            full_name = user_data["full_name"],
            role = "student"
        )

        # Lưu vào PostgreSQL
        db.add(new_user)
        db.commit()
        db.refresh(new_user)  # Lấy lại thông tin mới nhất (bao gồm cả ID tự tăng) từ DB lên RAM
        return new_user

    def login_user(self, db: Session, credentials:dict):
        """ Đăng nhập lấy thẻ TOKEN JWT
        Các tham số đầu vào:
        - db: Session là một đường ống kết nối xuống PostgreSQL.
              Nhờ có tham số này AuthService có khả năng dùng: db.query(),db.commit()...
        - credentials: dict: (Chứng chỉ/Thông tin chứng thực) có dạng 
            {"username": "truongdv", "password": "mật khẩu thô"}
        """

        # Tìm kiếm sinh viên theo tên đăng nhập 
        user=db.query(User).filter(User.username == credentials["username"]).first()

        if not user:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Không tìm thấy tên đăng nhập. Vui lòng nhập lại"
            )
        # Lấy mật khẩu từ trong db đã được băm ra, đưa vào máy băm kiểm tra với mật khẩu sinh viên nhập vào
        is_password_correct = verify_password(credentials["password"], user.hashed_password)
        if not is_password_correct:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Mật khẩu không chính xác. Vui lòng nhập lại"
            )
        # Nếu mật khẩu đúng tạo một thẻ TOKEN JWT
        token_payload = {
            "sub": user.username,
            "role": user.role
        }
        
        access_token = create_access_token(data=token_payload)

        return access_token