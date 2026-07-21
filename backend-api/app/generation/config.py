# Quản lý cấu hình (ngưỡng score, model name, endpoint)
from pydantic_settings import BaseSettings
    
class GenerationConfig(BaseSettings):
    #Tên mô hình đang sử dụng (dùng 1.5b để tối ưu tốc độ chạy trên CPU)
    MODEL_NAME:str = "qwen2.5:1.5b"

    #Địa chỉ kết nối với Ollama trong mạng Docker
    LLM_API_BASE:str = "http://ollama:11434/v1"
    
    #Chìa khóa ảo (do OLLAMA không bắt buộc nên ta để mặc định)
    LLM_API_KEY:str = "ollama"
    
    #Ngưỡng điểm tin cậy để chống ảo tưởng (nếu score nhỏ hơn ngưỡng này thì kết luận không có trong tài liệu)
    DEFAULT_SCORE_THRESHOLD:float = 0.60
    
    #Giới hạn độ dài câu trả lời tính theo token
    MAX_TOKENS:int = 512
    
    #Độ sáng tạo của AI trong câu trả lời
    TEMPERATURE:float = 0.15

    class Config:
        # Lệnh này bảo Python tự động tìm và đọc thêm các biến môi trường từ tệp .env (nếu có)
        env_file = ".env"
        extra = "ignore"

generation_config = GenerationConfig()