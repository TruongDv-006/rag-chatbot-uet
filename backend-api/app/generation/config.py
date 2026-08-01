# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings
    
class GenerationConfig(BaseSettings):
    # Tên model
    MODEL_NAME:str = "qwen2.5:7b"

    #Địa chỉ kết nối với Ollama trên Kaggle GPU
    LLM_API_BASE:str = "https://let-olympics-encoding-whether.trycloudflare.com/v1"
    
    #Chìa khóa ảo (do OLLAMA không bắt buộc nên ta để mặc định)
    LLM_API_KEY:str = "ollama"
    
    #Ngưỡng điểm tin cậy để chống ảo tưởng (nếu score nhỏ hơn ngưỡng này thì kết luận không có trong tài liệu)
    DEFAULT_SCORE_THRESHOLD:float = 0.45
    
    #Giới hạn độ dài câu trả lời tính theo token (tối ưu cho CPU)
    MAX_TOKENS:int = 1024
    
    #Độ sáng tạo của AI trong câu trả lời (0.0: Chuẩn xác tối đa, chống lan man, chống tự suy diễn)
    TEMPERATURE:float = 0.1

    class Config:
        # cái này dùng để Python tự động tìm và đọc thêm các biến môi trường từ tệp .env (nếu có)
        env_file = ".env"
        extra = "ignore"

generation_config = GenerationConfig()