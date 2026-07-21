from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session # pyrefly: ignore
from app.core.database import get_db # pyrefly: ignore
from app.services.auth_service import AuthService  # pyrefly:ignore


router = APIRouter()


class StudentRegisterRequest(BaseModel):
    username:str
    email: EmailStr
    password: str
    full_name: str

class LoginRequest(BaseModel):
    username: str
    password: str

#CỔNG TIẾP NHẬN ĐĂNG KÍ
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_student(request_data: StudentRegisterRequest, db: Session =Depends(get_db)):
    # Chuyển dữ liệu thô đóng gói thành dict
    user_dict = request_data.model_dump()

    auth_service = AuthService()
    new_user = auth_service.register_student(db=db, user_data=user_dict)

    return {
        "success":True,
        "message":f"Tài khoản của bạn đã được tạo thành công",
        "user_id": new_user.id
    }

#CỔNG TIẾP NHẬN ĐĂNG NHẬP
@router.post("/login")
def login_user(request_data: LoginRequest, db: Session =Depends(get_db)):
    # Chuyển dữ liệu thô đóng gói thành dict
    login_data = request_data.model_dump()

    auth_service = AuthService()
    token_str = auth_service.login_user(db=db, credentials = login_data)

    return {
        "access_token": token_str,
        "token_type":"bearer" #Quy chuẩn quốc tế (ai cầm thẻ cũng được)
    }