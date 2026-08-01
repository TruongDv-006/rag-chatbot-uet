# pyrefly: ignore [missing-import]
from qdrant_client.grpc import Range
import os
import re
import urllib.parse
# pyrefly: ignore [missing-import]
from app.generation.config import generation_config
# pyrefly: ignore [missing-import]
import requests
# pyrefly: ignore [missing-import]
import torch
# pyrefly: ignore [missing-import]
from qdrant_client import QdrantClient
# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer
from app.retriever.hybrid import HybridRetrieve # pyrefly: ignore
from app.generation.llm_client import OpenAICompatibleClient # pyrefly: ignore
from app.generation.orchestrator import RAGGenerator # pyrefly: ignore
from sqlalchemy.orm import Session # pyrefly: ignore
from app.models.user import User # pyrefly: ignore
from app.models.chat import ChatSession, ChatMessage # pyrefly: ignore

class ChatService:
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant_db:6333")
        self.collection_name = "uet_handbook"
        self.embed_model_name = "BAAI/bge-m3"
        self.llm_url = os.getenv("LLM_API_BASE", "http://ollama:11434/api")

        self._qdrant_client = None
        self._embed_model = None
        self._retriever = None
        self._generator = None

    @property
    def qdrant_client(self):
        if self._qdrant_client is None:
            self._qdrant_client = QdrantClient(url=self.qdrant_url)
        return self._qdrant_client

    @property
    def embed_model(self):
        if self._embed_model is None:
            self._embed_model = SentenceTransformer(self.embed_model_name, device="cuda" if torch.cuda.is_available() else "cpu")
        return self._embed_model

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = HybridRetrieve(
                self.qdrant_client,
                self.collection_name,
                self.embed_model_name
            )
        return self._retriever

    @property
    def generator(self):
        if self._generator is None:
            llm_client = OpenAICompatibleClient()
            self._generator = RAGGenerator(llm_client)
        return self._generator


    def _get_embedding(self, text:str):
        try:
            embedding = self.embed_model.encode(text).tolist()
            return embedding
        except Exception as e:
            print(f"[Embedding Warning] {e}")
        return []

    def _needs_query_rewriting(self, query: str, chat_history: list[dict] | None) -> bool:
        """
        Kiểm tra xem câu hỏi có thực sự cần phải Rewrite hay không.
        Chỉ Rewrite khi câu hỏi chứa từ khuyết ngữ cảnh (nó, đó, thế còn...) hoặc câu quá ngắn thiếu chủ ngữ.
        Giữ nguyên nếu câu hỏi đã có đầy đủ chủ đề độc lập.
        """
        if not chat_history:
            return False
        
        q_lower = query.lower().strip()
        
        # Các từ ngữ thể hiện sự phụ thuộc vào ngữ cảnh hội thoại trước
        context_triggers = ["nó", "đó", "cái này", "cái đó", "thế còn", "vậy còn", "ở đâu", "bao nhiêu", "bao giờ", "lúc nào", "khi nào"]
        has_trigger = any(re.search(rf"\b{re.escape(word)}\b", q_lower) for word in context_triggers)
        
        # Các từ khóa chủ đề độc lập rõ ràng
        standalone_domain_keywords = ["điểm", "học lại", "cải thiện", "bảo lưu", "học bổng", "thủ tục", "quy chế", "tốt nghiệp", "thẻ sinh viên"]
        has_standalone_domain = any(kw in q_lower for kw in standalone_domain_keywords)
        
        if has_standalone_domain and not has_trigger:
            return False
            
        return has_trigger or len(q_lower.split()) <= 4


    def process_message(self,db: Session, message:str, username:str, session_id:int | None=None):
        try:
            # Tìm ID của sinh viên đang Chat từ DATABASE
            user = db.query(User).filter(User.username==username).first()
            if not user:
                return {"reply": "Không tìm thấy thông tin thành viên hệ thống!", "source": {}}
            # Quản lý phiên chat
            current_session = None
            if session_id:
                #Nếu có session cũ lôi nó ra dùng tiếp (bảo mật theo user_id)
                current_session=db.query(ChatSession).filter(
                    ChatSession.id==session_id,
                    ChatSession.user_id ==user.id
                ).first()

            #Nếu không tìm thấy phiên cũ đưa ra chat mới tự động đặt tên
            if not current_session:
                words = message.split()
                auto_title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")

                current_session = ChatSession(
                    title = auto_title,
                    user_id = user.id
                )
                db.add(current_session)
                db.commit()
                db.refresh(current_session)

            # Lấy 1 tin nhắn gần nhất của phiên chat làm Context Window (trước khi thêm tin nhắn mới)
            recent_msgs = db.query(ChatMessage).filter(
                ChatMessage.session_id == current_session.id
            ).order_by(ChatMessage.created_at.desc()).limit(1).all()
            
            # Đảo ngược mảng để đúng thứ tự thời gian (từ cũ tới mới)
            recent_msgs.reverse()
            chat_history = [
                {"role": m.role, "content": m.content}
                for m in recent_msgs
            ]

            # Lưu câu hỏi của sinh viên xuống DB ChatMessage
            user_msg_obj = ChatMessage(
                role="student",
                content=message,
                session_id=current_session.id
            )
            db.add(user_msg_obj)

            # Kiểm tra nếu là câu chào hỏi/cảm ơn đơn giản -> Trả lời ngay bằng template cố định (không gọi LLM & RAG)
            clean_msg = message.strip().lower().strip(".!?,~😊👋")
            GREETING_RESPONSES = {
                "chào": "Xin chào! Tôi là Trợ lý tư vấn học vụ UET (Trường Đại học Công nghệ - ĐHQGHN). Tôi có thể giúp gì cho bạn về quy chế, chương trình đào tạo hay thủ tục học vụ?",
                "xin chào": "Xin chào! Tôi là Trợ lý tư vấn học vụ UET (Trường Đại học Công nghệ - ĐHQGHN). Tôi có thể giúp gì cho bạn về quy chế, chương trình đào tạo hay thủ tục học vụ?",
                "chào bạn": "Xin chào! Tôi là Trợ lý tư vấn học vụ UET (Trường Đại học Công nghệ - ĐHQGHN). Tôi có thể giúp gì cho bạn về quy chế, chương trình đào tạo hay thủ tục học vụ?",
                "hello": "Xin chào! Tôi là Trợ lý tư vấn học vụ UET (Trường Đại học Công nghệ - ĐHQGHN). Tôi có thể giúp gì cho bạn về quy chế, chương trình đào tạo hay thủ tục học vụ?",
                "hi": "Xin chào! Tôi là Trợ lý tư vấn học vụ UET (Trường Đại học Công nghệ - ĐHQGHN). Tôi có thể giúp gì cho bạn về quy chế, chương trình đào tạo hay thủ tục học vụ?",
                "cảm ơn": "Không có gì! Rất vui được hỗ trợ bạn. Nếu bạn có thêm thắc mắc gì về học vụ UET, đừng ngần ngại đặt câu hỏi nhé!",
                "cảm ơn bạn": "Không có gì! Rất vui được hỗ trợ bạn. Nếu bạn có thêm thắc mắc gì về học vụ UET, đừng ngần ngại đặt câu hỏi nhé!",
                "thanks": "Không có gì! Rất vui được hỗ trợ bạn. Nếu bạn có thêm thắc mắc gì về học vụ UET, đừng ngần ngại đặt câu hỏi nhé!",
                "thank you": "Không có gì! Rất vui được hỗ trợ bạn. Nếu bạn có thêm thắc mắc gì về học vụ UET, đừng ngần ngại đặt câu hỏi nhé!",
                "bạn là ai": "Tôi là Trợ lý tư vấn học vụ UET, hỗ trợ sinh viên Trường Đại học Công nghệ - ĐHQGHN tra cứu quy chế, quy định và các thủ tục học vụ.",
                "bạn tên gì": "Tôi là Trợ lý tư vấn học vụ UET, hỗ trợ sinh viên Trường Đại học Công nghệ - ĐHQGHN tra cứu quy chế, quy định và các thủ tục học vụ.",
                "bạn tên là gì": "Tôi là Trợ lý tư vấn học vụ UET, hỗ trợ sinh viên Trường Đại học Công nghệ - ĐHQGHN tra cứu quy chế, quy định và các thủ tục học vụ.",
                "tạm biệt": "Tạm biệt! Nếu bạn có thêm câu hỏi về học vụ, đừng ngần ngại liên hệ với tôi. Chúc bạn một ngày tốt lành!"
            }

            if clean_msg in GREETING_RESPONSES:
                reply_text = GREETING_RESPONSES[clean_msg]
                retrieved_docs = []
            else:
                # Kiểm tra xem có cần Viết lại câu hỏi độc lập (Query Rewriting) hay không
                if self._needs_query_rewriting(message, chat_history):
                    search_query = self.generator.rewrite_query(query=message, chat_history=chat_history)
                else:
                    search_query = message

                # Embedding câu hỏi đã viết lại thành vector để tìm kiếm RAG
                query_vector = self._get_embedding(search_query)
                retrieved_docs = self.retriever.search(
                    query=search_query,
                    query_vector=query_vector,
                    top_k=5
                )
                score_threshold = 0.0 if not query_vector else generation_config.DEFAULT_SCORE_THRESHOLD
                reply_text = self.generator.execute(
                    query=message,
                    retrieved_docs=retrieved_docs,
                    score_threshold=score_threshold,
                    chat_history=chat_history
                )

            # 1. Thu thập tất cả các file nguồn từ retrieved_docs
            unique_sources = []
            mapped_sources = {}
            for doc in retrieved_docs:
                raw_src = doc.get("source")
                if not raw_src or not str(raw_src).strip():
                    clean_src = "Sổ tay sinh viên UET"
                else:
                    clean_src = urllib.parse.unquote(str(raw_src)).strip()
                    if clean_src.endswith("_parsed.txt"):
                        clean_src = clean_src[:-11]
                    elif clean_src.endswith(".json"):
                        clean_src = clean_src[:-5]
                    elif clean_src.endswith(".txt"):
                        clean_src = clean_src[:-4]
                
                if clean_src not in unique_sources:
                    unique_sources.append(clean_src)

            for index, src in enumerate(unique_sources, start=1):
                mapped_sources[str(index)] = src

            # 2. Xử lý trích dẫn và tự động tạo Nguồn tham khảo chuẩn
            if reply_text and "Tôi không có đủ dữ liệu để trả lời" not in reply_text:
                # Bước A: Tự động bọc ngoặc [Tài liệu X] và xóa cụm lặp "Tài liệu [Tài liệu X]"
                reply_text = re.sub(r'(?<!\[)Tài liệu\s+(\d+)(?!\])', r'[Tài liệu \1]', reply_text, flags=re.IGNORECASE)
                reply_text = re.sub(r'(?:Tài\s+liệu\s+)+\[Tài\s+liệu\s+(\d+)\]', r'[Tài liệu \1]', reply_text, flags=re.IGNORECASE)

                # Bước B1: Xóa phần Nguồn/Tài liệu tham khảo do LLM tự sinh hoặc từ lịch sử hội thoại (nếu có)
                reply_text = re.sub(
                    r'\n*(?:📌|📍|👉|\*|\#)*\s*(?:\*\*|\#\#|\#)?\s*(?:Nguồn|Tài liệu)\s+tham\s+khảo\s*:?.*$', 
                    '', 
                    reply_text, 
                    flags=re.DOTALL | re.IGNORECASE
                ).strip()

                # Bước B2: Xóa triệt để các dòng link/định nghĩa thừa dạng [Tài liệu X]: http... ở cuối câu trả lời
                reply_text = re.sub(r'(\n+\s*\[Tài liệu\s*\d+\]\s*:\s*\S+)+$', '', reply_text, flags=re.IGNORECASE).strip()

                # Bước B3: Lọc sạch icon/emoji rác bị sót lại ở cuối
                reply_text = re.sub(r'[\n\s📌📍👉]+$', '', reply_text).strip()

                # Bước C: Quét tất cả chỉ số [Tài liệu X] có trong câu trả lời
                matches = re.findall(r'\[Tài liệu\s*(\d+)\]', reply_text, re.IGNORECASE)
                cited_indices_set = set()
                for m in matches:
                    cited_indices_set.add(int(m))
                cited_indices = sorted(list(cited_indices_set))

                # Nếu LLM trả lời chi tiết nhưng quên chèn [Tài liệu X] inline (và không phải câu chào xã giao)
                is_greeting = len(reply_text) < 45 or reply_text.lower().startswith("xin chào") or reply_text.lower().startswith("rất vui")
                if not cited_indices and unique_sources and not is_greeting:
                    cited_indices = list(range(1, len(unique_sources) + 1))

                # Bước D: Tạo lại danh sách Nguồn tham khảo đầy đủ và chuẩn xác
                source_lines = []
                if cited_indices:
                    for idx in cited_indices:
                        if 1 <= idx <= len(unique_sources):
                            clean_src = unique_sources[idx - 1]
                            source_lines.append(f"- **[Tài liệu {idx}]**: {clean_src}")

                if source_lines:
                    reply_text = reply_text.strip() + "\n\n**Nguồn tham khảo:**\n" + "\n".join(source_lines)

            ai_msg_obj = ChatMessage(
                role="assistant",
                content=reply_text,
                session_id=current_session.id
            )

            db.add(ai_msg_obj)
            db.commit()
            return {
                "session_id": current_session.id,
                "reply":reply_text,
                "source":mapped_sources
            }
        except Exception as e:
            db.rollback()
            return {"reply": f"Hệ thống đang gặp sự cố: {str(e)}", "source": {}}


    def get_user_sessions(self, db:Session, username:str):
        """Lấy danh sách các cuộc trò chuyện cũ để hiển thị lên Sidebar"""
        user = db.query(User).filter(User.username==username).first()

        if not user:
            return []

        sessions = db.query(ChatSession).filter(
            ChatSession.user_id==user.id
        ).order_by(ChatSession.created_at.desc()).all()

        return [
            {
                "id": s.id,
                "title": s.title,
                "created_at": s.created_at.isoformat()
            }
            for s in sessions
        ]


    def get_session_messages(self, db:Session, username:str, session_id:str):
        """Tải lại toàn bộ tin nhắn cũ khi bấm vào một cuộc trò chuyện ở Sidebar"""

        user = db.query(User).filter(User.username == username).first()
        if not user:
            return {"error": "Không tìm thấy người dùng"}


        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id
        ).first()

        if not session:
            return {"error": "Không tìm thấy phiên trò chuyện hoặc bạn không có quyền xem!"}
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()


        return [
            {
                "id": m.id,
                "role": m.role, # "student" hoặc "assistant"
                "content": m.content,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]

    def delete_session(self, db: Session, username: str, session_id: int):
        """Xóa một phiên trò chuyện của người dùng"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return {"error": "Không tìm thấy người dùng"}

        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id
        ).first()

        if not session:
            return {"error": "Không tìm thấy phiên trò chuyện"}

        db.delete(session)
        db.commit()
        return {"message": f"Đã xóa phiên trò chuyện thành công"}




