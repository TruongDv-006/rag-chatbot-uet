# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings
    
class GenerationConfig(BaseSettings):
    # Tên model
    MODEL_NAME:str = "qwen2.5:3b"

    #Địa chỉ kết nối với Ollama trong mạng Docker
    LLM_API_BASE:str = "http://ollama:11434/v1"
    
    #Chìa khóa ảo (do OLLAMA không bắt buộc nên ta để mặc định)
    LLM_API_KEY:str = "ollama"
    
    #Ngưỡng điểm tin cậy để chống ảo tưởng (nếu score nhỏ hơn ngưỡng này thì kết luận không có trong tài liệu)
    DEFAULT_SCORE_THRESHOLD:float = 0.60
    
    #Giới hạn độ dài câu trả lời tính theo token (tối ưu cho CPU)
    MAX_TOKENS:int = 512
    
    #Độ sáng tạo của AI trong câu trả lời (0.2: Chuẩn xác và tự nhiên)
    TEMPERATURE:float = 0.2

    class Config:
        # cái này dùng để Python tự động tìm và đọc thêm các biến môi trường từ tệp .env (nếu có)
        env_file = ".env"
        extra = "ignore"

generation_config = GenerationConfig()