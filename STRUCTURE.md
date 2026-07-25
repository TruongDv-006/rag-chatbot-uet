# 📁 Project Directory Structure

This document provides a detailed overview of the directory and file organization for the **UET Handbook Hybrid RAG Microservices** repository.

```text
rag-chatbot-uet/
├── docker-compose.yml           # Microservices orchestration configuration
├── pyrefly.toml                 # Code quality & linter configuration
├── nginx/                       # Gateway & Reverse Proxy configuration
│   ├── Dockerfile
│   └── nginx.conf
├── frontend-login/              # Authentication & User Registration UI
│   ├── Dockerfile
│   └── src/
│       ├── css/
│       ├── js/
│       └── index.html
├── frontend-user/               # Student Chatbot UI
│   ├── Dockerfile
│   └── src/
│       ├── assets/
│       ├── css/
│       ├── js/
│       └── index.html
├── frontend-admin/              # Admin Dashboard UI
│   ├── Dockerfile
│   └── src/
│       ├── assets/
│       ├── css/
│       ├── js/
│       └── index.html
├── backend-api/                 # Core FastAPI Server & RAG Engine
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # Application entry point
│       ├── core/                # DB connections & JWT security
│       ├── generation/          # RAG Orchestrator, LLM Client & Prompt Manager
│       ├── models/              # SQLAlchemy DB Models (User, Session, Message)
│       ├── retriever/           # Hybrid Retriever (BM25 + Dense + RRF + ReRanker)
│       ├── routes/              # API Endpoints (/chat, /auth, /admin)
│       ├── services/            # Business Logic Services
│       └── utils/               # Helper utilities
├── worker/                      # Async Celery Background Worker
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── task.py                  # Celery task definitions
│   ├── core/                    # DocumentProcessor for single files
│   ├── crawler/                 # Web Scraper & Document Parser
│   └── ingestion/               # Batch Ingester & Smart Chunker
└── infrastructure/              # Persistent Volume Mounts
    └── volumes/
        ├── minio_data/          # Storage for raw (.pdf, .docx) & web (.json) files
        ├── postgres_data/       # PostgreSQL relational database data
        └── qdrant_data/         # Qdrant Vector Database index & payloads
```

---

## 🧩 Component Overview

### 1. `nginx/`
- Serves as the primary Reverse Proxy Gateway.
- Routes incoming HTTP traffic on port `80`:
  - `/` -> `frontend-user` (Student Chat UI)
  - `/login` -> `frontend-login` (Auth UI)
  - `/admin` -> `frontend-admin` (Admin Dashboard UI)
  - `/api` -> `backend-api` (FastAPI Server on Port `8000`)

### 2. `frontend-login/`, `frontend-user/`, `frontend-admin/`
- Lightweight frontends built with pure **HTML5, Vanilla CSS, and JavaScript (ES6)** for zero build-overhead and fast delivery.
- **frontend-login:** User authentication, sign-up, and JWT token management.
- **frontend-user:** Interactive chatbot interface with real-time response rendering, source citation popups, and session management.
- **frontend-admin:** Administrative dashboard for uploading handbook documents, monitoring ingestion status, and viewing system data.

### 3. `backend-api/`
- Built with **FastAPI (Python 3.10)** for asynchronous execution and high performance.
- Houses the core **RAG Orchestrator**:
  - `retriever/`: Implements Hybrid Search combining BM25 keyword search (`underthesea` tokenizer) with Dense Vector Retrieval (Qdrant `bge-m3`), Reciprocal Rank Fusion (RRF), and ReRanking (`bge-reranker-base`).
  - `generation/`: Connects to Ollama Engine (`qwen2.5:3b`) via OpenAI API protocol, enforces anti-hallucination prompts, and attaches automatic source references.

### 4. `worker/`
- Asynchronous background processing worker executed by **Celery** with **Redis** as the message broker.
- Handles heavy computation tasks:
  - Web crawling student portal pages and storing clean `.json` output.
  - Smart document chunking (by Chapter, Section, Article) for `.pdf` and `.docx` files.
  - Computing 1024D embeddings (`BAAI/bge-m3`) and upserting payloads into Qdrant & MinIO.

### 5. `infrastructure/volumes/`
- Contains local persistent volumes for container state preservation:
  - `minio_data/`: S3-compatible object storage for original uploaded documents and raw web JSON files.
  - `postgres_data/`: Relational data storing user accounts, chat session history, and messages.
  - `qdrant_data/`: Vector storage index and metadata payloads.
