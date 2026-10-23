# Nextjs-RAG-Notebook (NotebookLM Clone) 🚀

A modern, AI-powered document chat app using Next.js 15.5. Upload PDFs or SVGs, extract website content, and chat with your documents using OpenAI GPT models and semantic vector search.

---

## ✨ Key Features

- **Document Upload**: Drag & drop PDFs/SVGs for instant processing
- **Web Content Extraction**: Enter URLs to extract and analyze website content
- **AI-Powered Chat**: Ask questions about your docs and get streaming, context-aware replies
- **Semantic Search**: Uses Qdrant vector DB for lightning-fast, relevant retrieval
- **Modern UI**: Responsive, clean interface built with Tailwind CSS
- **Live Processing**: Real-time embedding and chunking for instant feedback

---

## 🛠️ Tech Stack

- **Frontend**: Next.js 15.5 (App Router), React 19, Tailwind CSS, Lucide Icons
- **AI/ML**: OpenAI GPT-3.5/4, OpenAI Embeddings
- **Vector DB**: Qdrant Cloud
- **Document Handling**: PDF2JSON, Cheerio (web scraping)
- **Deployment**: Vercel-ready

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- OpenAI API Key
- Qdrant Cloud account & API Key

### Install & Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/shivam-911/Nextjs-RAG-Notebook.git
   cd Nextjs-RAG-Notebook
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Configure environment variables:
   ```bash
   cp .env.example .env.local
   ```
   Edit `.env.local` with your API credentials:
   ```
   OPENAI_API_KEY=your_openai_api_key
   QDRANT_URL=your_qdrant_cloud_url
   QDRANT_API_KEY=your_qdrant_api_key
   NEXT_PUBLIC_APP_URL=http://localhost:3000
   ```
4. Start the dev server:
   ```bash
   npm run dev
   ```
   Visit [http://localhost:3000](http://localhost:3000) to use the app.

---

## 📂 Project Structure

```
├── app/                    # Next.js App Router & pages
│   ├── api/                # API endpoints
│   ├── globals.css         # Global styles
│   ├── layout.jsx          # Root layout
│   └── page.jsx            # Main page
├── components/             # Reusable React components
├── lib/                    # Document & AI utilities
├── next.config.js          # Next.js config
├── tailwind.config.js      # Tailwind CSS config
└── package.json            # Dependencies & scripts
```

---

## 🧑‍💻 Usage

1. **Upload** documents (PDF/SVG) or paste a website URL.
2. **Process**: Files/websites are chunked and embedded in Qdrant.
3. **Chat**: Ask questions about uploaded content; AI searches and streams relevant answers.
4. **Manage**: View, delete, or clear documents from your workspace.

---

## ⚙️ Environment Config

**OpenAI API Key**
- Get yours from [OpenAI Platform](https://platform.openai.com/)
- Add to `.env.local` as `OPENAI_API_KEY`

**Qdrant Cloud**
- Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
- Create a cluster, grab the URL & API key
- Add to `.env.local` as `QDRANT_URL` & `QDRANT_API_KEY`

---

## 🚢 Deployment

**Vercel (Recommended):**
1. Push to GitHub
2. Import repo in [Vercel](https://vercel.com)
3. Add environment variables in dashboard
4. Deploy!

**Manual:**
```bash
npm run build
npm start
```

---

## 🔌 API Endpoints

- `POST /api/documents/upload` — Upload & process files
- `POST /api/documents/url` — Extract website content
- `GET /api/documents` — List uploaded docs
- `DELETE /api/documents` — Remove all docs
- `DELETE /api/documents/[id]` — Remove specific doc
- `POST /api/chat` — AI chat with streaming response

---

## 🏗️ Features in Depth

- **PDF/SVG Processing**: Extracts and chunks text for embedding
- **Web Scraping**: Uses Cheerio for smart content extraction
- **Semantic Search**: Embeds with OpenAI, stores in Qdrant, retrieves via similarity
- **Streaming Chat**: Contextual answers with source attribution

---

## 📄 License

MIT — Free for personal & commercial use.

---

## 💡 Need Help?

1. Double-check API keys and environment variables
2. Ensure OpenAI/Qdrant accounts are active
3. Review console/logs for errors
4. Open a GitHub Issue for support

---

Enjoy building with Nextjs-RAG-Notebook! 🚀