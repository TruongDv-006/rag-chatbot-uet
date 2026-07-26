from sqlalchemy.orm import Session # pyrefly:ignore
from app.models.user import User #pyrefly:ignore
from app.utils.security import get_password_hash # pyrefly:ignore

def seed_default_users(db: Session):
    """Hàm tự động tạo tài khoản Admin và Sinh viên mặc định nếu chưa tồn tại"""
    default_users = [
        {
            "username": "admin1",
            "email": "admin1@vnu.edu.vn",
            "full_name": "Quản trị viên UET",
            "password": "Admin@123",
            "role": "admin"
        },
        {
            "username": "sinhvien1",
            "email": "sinhvien1@vnu.edu.vn",
            "full_name": "Sinh viên UET 1",
            "password": "Student@123",
            "role": "student"
        },
        {
            "username": "sinhvien2",
            "email": "sinhvien2@vnu.edu.vn",
            "full_name": "Sinh viên UET 2",
            "password": "Student@123",
            "role": "student"
        }
    ]

    try:
        for user_data in default_users:
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing:
                print(f"[Seed] Tạo tài khoản: {user_data['username']} ({user_data['role']})")
                hashed_pwd = get_password_hash(user_data["password"])
                db_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    full_name=user_data["full_name"],
                    hashed_password=hashed_pwd,
                    role=user_data["role"]
                )
                db.add(db_user)
        db.commit()
    except Exception as e:
        db.rollback()