# Interface và các class con kết nối đến Ollama/vLLM (Strategy Pattern)
from abc import ABC, abstractmethod
from openai import OpenAI
from app.generation.config import generation_config # pyrefly: ignore [missing-import]

class LLMClient(ABC):
    """
    Interface định nghĩa chung cho tất cả các AI
    Nó buộc các lớp con khi kế thừa từ interface này đều 
    phải viết 1 hàm "generate"
    """
    @abstractmethod
    def generate(self, messages:list[dict[str, str]]):
        pass


class OpenAICompatibleClient(LLMClient):
    """
    Lớp này kế thừa từ LLMClient
    và dùng thư viện openai để nói chuyện với Ollama
    """
    def __init__(self):
        
        pass

    def generate(self, messages:list[dict[str, str]]):

        pass