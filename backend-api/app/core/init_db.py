from sqlalchemy.orm import Session # pyrefly:ignore
from app.models.user import User #pyrefly:ignore
from app.models.security import get_password_hash # pyrefly:ignore

def seed_default_users(db: Session):
    """Hàm tự động tạo tài khoản Admin và Sinh viên mặc định nếu chưa tồn tại"""
    default_users=[
        {
            "username": "admin1",
            "email": "admin1@vnu.edu.vn",
            "full_name": "Quản trị viên UET1",
            "password": "123456", 
            "role": "admin" # admin
        },
        {
            "username": "admin2",
            "email": "admin2@vnu.edu.vn",
            "full_name": "Quản trị viên UET",
            "password": "123456", 
            "role": "student" # admin
        },
        {
            "username": "sinhvien1",
            "email": "sinhvien1@vnu.edu.vn",
            "full_name": "Sinh viên UET1",
            "password": "123456", 
            "role": "student" # student
        },
        {
            "username": "sinhvien2",
            "email": "sinhvien2@vnu.edu.vn",
            "full_name": "Sinh viên UET2",
            "password": "123456",
            "role": "student" # student
        }
    ]
    
    for user_data in default_users:
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()

        if not existing_user:
            print(f"[Database Seed] Đang khởi tạo tài khoản mặc định: {user_data['username']}...")
            
            # Băm mật khẩu thô trước khi lưu xuống Postgre
            hashed_pwd = get_password_hash(user_data["password"])
            
            db_user = User(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hashed_pwd,
                role=user_data["role"]
            )
            db.add(db_user)
            
    # Lưu xuống Postgre
    db.commit()
    print("[Database Seed] Hoàn thành quá trình kiểm tra và khởi tạo tài khoản mặc định!")