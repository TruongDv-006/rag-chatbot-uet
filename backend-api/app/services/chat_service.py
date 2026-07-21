from qdrant_client.grpc import Range
import os
import requests
from qdrant_client import QdrantClient
from app.retriever.hybrid import HybridRetrieve # pyrefly: ignore
from app.generation.llm_client import OpenAICompatibleClient # pyrefly: ignore
from app.generation.orchestrator import RAGGenerator # pyrefly: ignore
from sqlalchemy.orm import Session # pyrefly: ignore
from app.models.user import User # pyrefly: ignore
from app.models.chat import ChatSession, ChatMessage # pyrefly: ignore

class ChatService:
    def __init__(self):
        qdrant_url = os.getenv("QDRANT_URL","http://qdrant_db:6333")

        self.qdrant_client = QdrantClient(url=qdrant_url)
        self.collection_name = "uet_handbook"
        self.embed_model = "BAAI/bge-m3"
        self.llm_url = os.getenv("LLM_API_BASE","http://ollama:11434/api")

        self.retriever = HybridRetrieve(
            self.qdrant_client,
            self.collection_name,
            self.embed_model
        )

        self.llm_client = OpenAICompatibleClient()
        self.generator = RAGGenerator(self.llm_client)


    def _get_embedding(self, text:str):
        try:
            url = f"{self.llm_url}/embeddings"
            res = requests.post(url, json={"model": self.embed_model, "prompt": text}, timeout=3)
            if res.ok:
                return res.json().get("embedding", [])
        except Exception as e:
            print(f"[Embedding Warning] {e}")
        return []


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

            #Lưu câu hỏi của sinh viên xuống DB ChatMessage
            user_msg_obj = ChatMessage(
                role="student",
                content=message,
                session_id=current_session.id
            )
            db.add(user_msg_obj)

            # Embedding câu hỏi thành vector
            query_vector = self._get_embedding(message)
            retrieved_docs = self.retriever.search(
                query = message,
                query_vector = query_vector,
                top_k=5
            )

            # Nếu không có embedding (Qdrant chưa có dữ liệu), hạ ngưỡng để LLM vẫn được gọi
            score_threshold = 0.0 if not query_vector else 0.3
            reply_text = self.generator.execute(
                query = message,
                retrieved_docs=retrieved_docs,
                score_threshold=score_threshold
            )

            #
            valid_docs = [doc for doc in retrieved_docs if doc.get("score",0.0) >= score_threshold]
            mapped_sources = {}

            for index, doc in enumerate(valid_docs, start=1):
                mapped_sources[str(index)]=doc.get("source","Sổ tay UET")

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




