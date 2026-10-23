# 📚 DocuGraph RAG — Nền Tảng Trích Xuất & Hỏi Đáp Tài Liệu Thông Minh

> **DocuGraph RAG** là hệ thống hỏi đáp tài liệu thông minh kết hợp **GraphRAG** (Retrieval-Augmented Generation trên đồ thị tri thức), **OCR đa mô hình**, và **Google Gemini AI** — được xây dựng theo kiến trúc full-stack hiện đại.

---

## 🌟 Tổng Quan Dự Án

| Thành phần | Công nghệ |
|---|---|
| **Frontend** | Next.js 15, React 19, TailwindCSS 3 |
| **Backend** | Python 3.12+, FastAPI, Uvicorn |
| **AI / LLM** | Google Gemini 2.5 Flash (`gemini-2.5-flash`) |
| **Embedding** | Google Gemini Embedding (`gemini-embedding-001`, dim=768) |
| **Vector DB / Graph DB** | Neo4j 5.12 (vector index + Knowledge Graph) |
| **Relational DB** | PostgreSQL 16 (async via SQLAlchemy + asyncpg) |
| **OCR** | PaddleOCR v2.8 (PP-OCRv4/v5 mobile, hỗ trợ tiếng Việt) |
| **Container** | Docker + Docker Compose |

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                      │
│  AuthModal │ ChatInterface │ DocumentUpload │ KnowledgeGraph     │
│  DocumentList │ SourceViewer │ LoadingSpinner                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │ REST API / SSE Streaming
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                           │
│                                                                 │
│  Routers: /auth  /notebooks  /sources  /chat  /graph           │
│                                                                 │
│  Services:                                                      │
│  ┌───────────────┐  ┌──────────────────┐  ┌─────────────────┐  │
│  │ auth_service  │  │ document_processor│  │  rag_service    │  │
│  │ (JWT + OAuth2)│  │ (PDF/OCR/URL)    │  │ (Search + LLM)  │  │
│  └───────────────┘  └──────────────────┘  └─────────────────┘  │
│  ┌───────────────────────┐  ┌────────────────────────────────┐  │
│  │   embedding_service   │  │       neo4j_service            │  │
│  │ (Gemini Embeddings)   │  │  (Graph + Vector Store)        │  │
│  └───────────────────────┘  └────────────────────────────────┘  │
└──────────┬─────────────────────────────┬───────────────────────┘
           ▼                             ▼
  ┌─────────────────┐         ┌──────────────────────┐
  │  PostgreSQL 16  │         │      Neo4j 5.12       │
  │  (Users,        │         │  (Chunks + Embeddings │
  │  Notebooks,     │         │   + Knowledge Graph)  │
  │  Sources,       │         │  Vector Index: cosine │
  │  ChatMessages)  │         │  dim = 768            │
  └─────────────────┘         └──────────────────────┘
```

---

## ⚙️ Công Nghệ & Ngôn Ngữ Kỹ Thuật Chi Tiết

### 🐍 Backend — Python 3.12+

#### Framework & API
| Thư viện | Phiên bản | Vai trò |
|---|---|---|
| **FastAPI** | >= 0.115 | Web framework async, tự động sinh OpenAPI docs |
| **Uvicorn** | >= 0.30 | ASGI server chạy FastAPI |
| **python-multipart** | >= 0.0.9 | Xử lý file upload (`multipart/form-data`) |

#### AI / RAG Pipeline
| Thư viện | Phiên bản | Vai trò |
|---|---|---|
| **LangChain** | >= 0.3 | Orchestration framework cho RAG |
| **langchain-google-genai** | >= 2.0 | Kết nối Google Gemini (Chat + Embedding) |
| **langchain-community** | >= 0.3 | Các community integrations |
| **langchain-text-splitters** | >= 0.3 | `RecursiveCharacterTextSplitter` chia nhỏ văn bản |
| **google-genai** | (transitive) | Google GenAI SDK cho structured output (KG extraction) |

**Model sử dụng:**
- 🤖 **LLM:** `gemini-2.5-flash` — trả lời câu hỏi, trích xuất knowledge graph (structured JSON)
- 🔢 **Embedding:** `models/gemini-embedding-001` — tạo vector 768 chiều cho semantic search

#### Cơ Sở Dữ Liệu
| Thư viện | Phiên bản | Vai trò |
|---|---|---|
| **SQLAlchemy[asyncio]** | >= 2.0 | ORM async cho PostgreSQL |
| **asyncpg** | >= 0.30 | Async PostgreSQL driver |
| **neo4j** | >= 5.12.0 | Neo4j Python driver (Bolt protocol) |

#### Xử Lý Tài Liệu
| Thư viện | Phiên bản | Vai trò |
|---|---|---|
| **PyMuPDF (fitz)** | >= 1.24 | Đọc & render PDF sang ảnh |
| **PaddleOCR** | >= 2.8 | OCR đa ngôn ngữ (PP-OCRv4/v5 mobile) |
| **PaddlePaddle** | >= 2.6 | Deep learning framework của PaddleOCR |
| **Pillow** | >= 10.0 | Xử lý ảnh (Image open/resize) |

**Pipeline OCR:**
1. **PDF có text:** Dùng PyMuPDF `page.get_text()` trực tiếp (nhanh, không cần OCR)
2. **PDF scan (ảnh):** Render từng trang → 75 DPI PNG → PaddleOCR song song (`ProcessPoolExecutor`, tối đa 3 workers)
3. **Image file:** PaddleOCR trực tiếp
4. **Gemini Vision:** Fallback OCR cho ảnh phức tạp (async)

#### Web Scraping
| Thư viện | Phiên bản | Vai trò |
|---|---|---|
| **httpx** | >= 0.27 | Async HTTP client (scraping URL, gọi Google API) |
| **BeautifulSoup4** | >= 4.12 | Parse HTML, extract nội dung trang web |

#### Xác Thực & Bảo Mật
| Thư viện | Phiên bản | Vai trò |
|---|---|---|
| **PyJWT** | >= 2.8.0 | Tạo & xác thực JWT token (HS256) |
| **passlib[bcrypt]** | >= 1.7.4 | Password hashing |
| **bcrypt** | >= 4.0.0 | bcrypt implementation |
| **email-validator** | >= 2.0.0 | Validate email format |

**Auth flow:**
- **Email/Password:** bcrypt hash → JWT access token (7 ngày hết hạn)
- **Google OAuth2:** Verify Google ID Token qua `oauth2.googleapis.com/tokeninfo` → JWT

#### Tiện Ích
| Thư viện | Phiên bản | Vai trò |
|---|---|---|
| **pydantic-settings** | >= 2.0 | Đọc config từ `.env` file |
| **python-dotenv** | >= 1.0 | Load `.env` variables |
| **aiofiles** | >= 24.0 | Async file I/O |
| **Pydantic** | (transitive) | Data validation, Schema models |

#### Dev / Test
| Thư viện | Vai trò |
|---|---|
| **pytest** >= 8.0 | Unit/integration testing |
| **pytest-asyncio** >= 0.24 | Async test support |
| **uv** | Fast Python package manager (thay pip) |

---

### ⚛️ Frontend — JavaScript / Next.js

#### Core Framework
| Package | Phiên bản | Vai trò |
|---|---|---|
| **Next.js** | 15.5.0 | React full-stack framework (App Router) |
| **React** | 19.0.0 | UI library |
| **react-dom** | 19.0.0 | React DOM renderer |

#### UI & Styling
| Package | Phiên bản | Vai trò |
|---|---|---|
| **TailwindCSS** | 3.4.15 | Utility-first CSS framework |
| **PostCSS** | >= 8.4 | CSS preprocessor (autoprefixer) |
| **autoprefixer** | >= 10.4 | Tự động thêm vendor prefix CSS |
| **clsx** | >= 2.1 | Conditional class names |
| **tailwind-merge** | >= 2.5 | Merge Tailwind classes không bị conflict |
| **class-variance-authority** | >= 0.7 | Component variant management |
| **lucide-react** | >= 0.454 | Icon library (SVG icons) |
| **Google Fonts (Inter)** | — | Typography — hỗ trợ `latin` + `vietnamese` |

#### Tính Năng Đặc Biệt
| Package | Phiên bản | Vai trò |
|---|---|---|
| **react-force-graph-2d** | >= 1.29 | Render Knowledge Graph 2D interactively (Canvas) |
| **uuid** | >= 11.1 | Generate UUID cho client-side state |

#### Dev Tools
| Package | Phiên bản | Vai trò |
|---|---|---|
| **TypeScript** | 5.7.2 | Type checking (devDependency) |
| **ESLint** | 9.16 | Linting JavaScript/JSX |
| **eslint-config-next** | 15.5.0 | Next.js ESLint config |

---

### 🗄️ Cơ Sở Dữ Liệu

#### PostgreSQL 16
Quản lý dữ liệu quan hệ qua SQLAlchemy async ORM:

| Bảng | Mô tả |
|---|---|
| `users` | Tài khoản người dùng (local + Google OAuth) |
| `notebooks` | Notebook chứa tài liệu và lịch sử chat |
| `sources` | Tài liệu nguồn (PDF, ảnh, URL) với trạng thái xử lý |
| `chat_messages` | Lịch sử hội thoại RAG |

#### Neo4j 5.12
Lưu trữ đồ thị tri thức (Knowledge Graph) và vector embeddings:

| Node | Mô tả |
|---|---|
| `:Notebook` | Node đại diện notebook |
| `:Source` | Node đại diện tài liệu nguồn |
| `:Chunk` | Đoạn văn bản (có vector embedding 768-dim) |
| `:Person/:Organization/:Concept/...` | Entity được Gemini trích xuất |

| Relationship | Mô tả |
|---|---|
| `(Source)-[:BELONGS_TO]->(Notebook)` | Tài liệu thuộc notebook |
| `(Chunk)-[:PART_OF]->(Source)` | Đoạn văn thuộc tài liệu |
| `(Entity)-[:MENTIONED_IN]->(Chunk)` | Entity xuất hiện trong đoạn văn |
| `(Entity)-[DYNAMIC_REL]->(Entity)` | Quan hệ giữa các entity |

**Vector Index:** `chunk_vector_index` — cosine similarity, 768 dimensions (HNSW)

---

### 🐳 Hạ Tầng & Triển Khai

| Công nghệ | Vai trò |
|---|---|
| **Docker Compose** | Orchestrate PostgreSQL + Neo4j containers |
| **PostgreSQL 16-alpine** | Relational DB (port 5432) |
| **Neo4j 5.12.0 + APOC** | Graph DB (HTTP: 7474, Bolt: 7687) |

---

## 📁 Cấu Trúc Thư Mục

```
THUCTAP/
├── backend/                       # Python FastAPI Backend
│   ├── app/
│   │   ├── main.py               # Entry point FastAPI app
│   │   ├── config.py             # Pydantic Settings từ .env
│   │   ├── database.py           # SQLAlchemy async engine + session
│   │   ├── models/
│   │   │   ├── user.py           # User SQLAlchemy model
│   │   │   └── notebook.py       # Notebook, Source, ChatMessage models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── auth.py           # POST /auth/register, /auth/login, /auth/google
│   │   │   ├── notebooks.py      # CRUD notebooks
│   │   │   ├── sources.py        # Upload PDF/image/URL, serve file
│   │   │   ├── chat.py           # POST /chat (RAG stream)
│   │   │   └── graph.py          # GET /graph (Knowledge Graph data)
│   │   └── services/
│   │       ├── auth_service.py        # JWT + bcrypt + Google OAuth2
│   │       ├── document_processor.py  # PDF/OCR/URL text extraction
│   │       ├── embedding_service.py   # Gemini Embeddings + store to Neo4j
│   │       ├── neo4j_service.py       # Neo4j CRUD + KG extraction via Gemini
│   │       ├── notebook_service.py    # Business logic notebooks/sources
│   │       └── rag_service.py         # Vector search + Gemini chat (RAG)
│   ├── RAGS/                     # Đánh giá RAGAS
│   │   ├── 25-trang.pdf          # Tài liệu test
│   │   └── *.xlsx                # Kết quả đánh giá
│   ├── evaluate_ragas.py         # Script đánh giá RAG với RAGAS framework
│   ├── generate_evaluation_excel.py  # Export kết quả ra Excel
│   ├── pyproject.toml            # Khai báo dependencies (uv)
│   └── docker-compose.yml        # PostgreSQL + Neo4j containers
│
└── frontend/                      # Next.js Frontend
    ├── app/
    │   ├── layout.jsx            # Root layout (Inter font, AuthProvider)
    │   ├── page.jsx              # Main page (SPA-style routing)
    │   └── globals.css           # Global CSS + Tailwind base
    ├── components/
    │   ├── AuthModal.jsx         # Login/Register modal (email + Google)
    │   ├── ChatInterface.jsx     # Chat với AI, hiển thị streaming
    │   ├── DocumentList.jsx      # Danh sách tài liệu trong notebook
    │   ├── DocumentUpload.jsx    # Upload PDF/image/URL
    │   ├── KnowledgeGraph.jsx    # Visualize Knowledge Graph 2D
    │   ├── LoadingSpinner.jsx    # Loading indicator
    │   └── SourceViewer.jsx      # Xem nội dung / preview tài liệu
    ├── context/
    │   └── AuthContext.jsx       # React Context quản lý auth state
    ├── lib/                      # Utility functions
    ├── next.config.js            # Next.js configuration
    ├── tailwind.config.js        # Tailwind theme config
    └── package.json
```

---

## 🚀 Tính Năng Chính

### 1. 📄 Xử Lý Tài Liệu Đa Dạng
- **PDF có text:** Trích xuất trực tiếp bằng PyMuPDF (tức thì)
- **PDF scan:** OCR song song bằng PaddleOCR PP-OCRv4 mobile (75 DPI, tối đa 3 workers)
- **Ảnh (PNG, JPG, WEBP...):** PaddleOCR với language detection (`vi` mặc định)
- **URL:** Scraping với httpx + BeautifulSoup, tự động loại bỏ nav/footer/script

### 2. 🧠 GraphRAG Pipeline
```
Tài liệu → Text Chunks (1000 chars, overlap 200)
         → Gemini Embedding (768-dim vectors)
         → Neo4j vector store
         → Gemini Entity/Relation Extraction (structured JSON)
         → Neo4j Knowledge Graph

Khi hỏi:
Query → Embed query → Vector search Neo4j (cosine, top-5)
      → Graph traversal (entities linked to top chunks)
      → Build context (chunks + KG relationships)
      → Gemini 2.5 Flash → Streaming SSE response
```

### 3. 🔐 Xác Thực Đa Phương Thức
- **Email/Password:** bcrypt hash → JWT (HS256, 7 ngày)
- **Google OAuth2:** Verify ID Token → auto-create/link account → JWT

### 4. 📊 Trực Quan Hóa Knowledge Graph
- Component `KnowledgeGraph.jsx` dùng `react-force-graph-2d`
- Render 2D interactive graph với nodes (entities) và edges (relationships)
- Data từ API `/api/notebooks/{id}/graph`

### 5. 📈 Đánh Giá RAGAS
- Script `evaluate_ragas.py` đánh giá chất lượng RAG pipeline
- Metrics: Faithfulness, Answer Relevancy, Context Precision/Recall
- Export kết quả ra file Excel (`Bao_Cao_Danh_Gia_RAGAS_25_Trang.xlsx`)

---

## 🔌 API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| `POST` | `/auth/register` | Đăng ký tài khoản |
| `POST` | `/auth/login` | Đăng nhập, nhận JWT |
| `POST` | `/auth/google` | Đăng nhập bằng Google |
| `GET` | `/api/notebooks` | Danh sách notebooks |
| `POST` | `/api/notebooks` | Tạo notebook mới |
| `DELETE` | `/api/notebooks/{id}` | Xóa notebook |
| `POST` | `/api/notebooks/{id}/sources/upload` | Upload PDF/image |
| `POST` | `/api/notebooks/{id}/sources/url` | Thêm URL |
| `GET` | `/api/notebooks/{id}/sources` | Danh sách sources |
| `DELETE` | `/api/notebooks/{id}/sources/{sid}` | Xóa source |
| `GET` | `/api/notebooks/{id}/sources/{sid}/file` | Preview/download file |
| `POST` | `/api/notebooks/{id}/chat` | Chat RAG (SSE stream) |
| `GET` | `/api/notebooks/{id}/chat` | Lịch sử chat |
| `GET` | `/api/notebooks/{id}/graph` | Knowledge Graph data |
| `GET` | `/api/health` | Health check |

---

## ⚡ Cài Đặt & Chạy

### Yêu Cầu
- Python >= 3.12
- Node.js >= 18
- Docker & Docker Compose
- Google Gemini API Key

### 1. Khởi động Database
```bash
docker-compose up -d
```
PostgreSQL chạy tại `localhost:5432`, Neo4j tại `localhost:7474` (HTTP) / `7687` (Bolt).

### 2. Cấu Hình Backend
```bash
cd backend
cp .env.example .env
# Chỉnh sửa .env: thêm GEMINI_API_KEY và các thông số cần thiết
```

### 3. Chạy Backend
```bash
cd backend
# Dùng uv (khuyến nghị):
uv run uvicorn app.main:app --reload --port 8000

# Hoặc pip:
pip install -e .
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### 4. Chạy Frontend
```bash
cd frontend
npm install
npm run dev
```
Truy cập: http://localhost:3000

---

## 🔧 Biến Môi Trường

### Backend (`.env`)
```env
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/notebooklm

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4j_password

# RAG Settings
CHAT_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=models/gemini-embedding-001
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RAG_TOP_K=5

# PaddleOCR
PADDLE_OCR_LANG=vi
PADDLE_USE_GPU=false

# Auth (JWT)
JWT_SECRET_KEY=change-me-to-a-strong-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Google OAuth2 (optional)
GOOGLE_CLIENT_ID=your_google_client_id

# CORS
CORS_ORIGINS=http://localhost:3000
```

### Frontend (`.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🧪 Testing & Đánh Giá

```bash
# Unit tests backend
cd backend
uv run pytest tests/ -v

# Đánh giá RAGAS
uv run python evaluate_ragas.py

# Xuất báo cáo Excel
uv run python generate_evaluation_excel.py
```

---

## 🛠️ Tóm Tắt Công Nghệ

```
Backend:   Python 3.12 · FastAPI · SQLAlchemy · asyncpg · LangChain
           Gemini 2.5 Flash · Gemini Embedding 001 · PaddleOCR PP-OCRv4
           Neo4j 5.12 · PostgreSQL 16 · PyJWT · bcrypt · httpx · PyMuPDF

Frontend:  Next.js 15 · React 19 · TailwindCSS 3 · react-force-graph-2d
           lucide-react · clsx · Google Fonts (Inter)

Infra:     Docker Compose · Neo4j APOC · RAGAS evaluation
```

---

*Được phát triển như đề tài thực tập — DocuGraph RAG v0.1.0*
