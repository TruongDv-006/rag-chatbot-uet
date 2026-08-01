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
    def generate(self, messages: list, model_name: str | None = None) -> str:
        pass


class OpenAICompatibleClient(LLMClient):
    """
    Lớp này kế thừa từ LLMClient
    và dùng thư viện openai để nói chuyện với Ollama
    """
    def __init__(self):
        """
        Khởi tạo 1 kết nối(Client) thông qua thư viện openai
        Tuy nhiên không hướng ra Internet của OpenAI mà hướng vào "ollama" trong Docker
        """
        self.client = OpenAI(
            base_url = generation_config.LLM_API_BASE,
            api_key = generation_config.LLM_API_KEY
        )
        self.model_name = generation_config.MODEL_NAME

    def generate(self, messages: list, model_name: str | None = None) -> str:
        """
        Hàm này gửi dữ liệu qua Ollama và nhận câu trả lời về.
        """
        target_model = model_name or self.model_name
        try:
            # Gửi câu hỏi
            response = self.client.chat.completions.create(
                model = target_model,
                messages = messages,
                max_tokens = generation_config.MAX_TOKENS,
                temperature = generation_config.TEMPERATURE
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as e:
            raise RuntimeWarning(f"Lỗi kết nối đến Ollama Engine ({target_model}): {e}")