from datetime import datetime, timedelta, timezone
import os
# pyrefly: ignore [missing-import]
import bcrypt as _bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError # pyrefly:ignore

#Các thông số cấu hình thẻ Token JWT
SECRET_KEY = os.getenv("SECRET_KEY", "scretkey")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

def get_password_hash(password: str) -> str:
    """Băm mật khẩu bằng bcrypt trực tiếp (bỏ qua passlib để tránh bug)"""
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu có khớp hash không"""
    return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data:dict):
    """Hàm in thẻ JWT Token cấp cho sinh viên khi đăng nhập thành công"""
    to_encode=data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm = ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
def get_current_user(token : str = Depends(oauth2_scheme)):
    """
    Hàm này lấy Token từ tay người gọi API sau đó kiểm tra thẻ JWT 
    và trả về tên tài khoản (Username/email) nếu hợp lệ
    """

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Thẻ không chứa thông tin định danh hợp lệ!"
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail = "Thẻ Token JWT đã hết hạn hoặc bị fake"
        )

def get_current_admin(token: str = Depends(oauth2_scheme)):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")

        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Thẻ không chứa thông tin định danh hợp lệ!"
            )
        
        if role != "admin":
            raise HTTPException(
                status_code=403, 
                detail="Bạn không có quyền truy cập vào khu vực dành cho Admin"
            )
        return username


    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Thẻ Token JWT đã hết hạn hoặc bị fake"
        )