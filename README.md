# AICTE Interview Trainer Agent
### Problem Statement No. 22 | Powered by IBM Granite & IBM Watsonx.ai

> An AI-powered Interview Trainer that uses **RAG (Retrieval-Augmented Generation)** and **IBM Granite** (IBM Cloud Lite) to generate tailored interview question sets, model answers, and preparation strategies based on a candidate's profile.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AICTE Interview Trainer Agent                    │
│                                                                      │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────────────────────┐ │
│  │  Resume  │──▶│ Resume Parser│──▶│                             │ │
│  │  Upload  │   │  (PDF/TXT)   │   │   RAG Pipeline              │ │
│  └──────────┘   └──────────────┘   │                             │ │
│                                    │  ┌─────────────────────┐    │ │
│  ┌──────────┐                      │  │  ChromaDB Vector DB  │    │ │
│  │  Profile │──────────────────────│  │  (SentenceTransformer│    │ │
│  │  Input   │                      │  │   Embeddings)        │    │ │
│  └──────────┘                      │  └──────────────────────┘    │ │
│                                    │            │                  │ │
│                                    │  ┌─────────▼──────────┐      │ │
│                                    │  │  IBM Watsonx.ai     │      │ │
│                                    │  │  IBM Granite LLM    │      │ │
│                                    │  │  (IBM Cloud Lite)   │      │ │
│                                    │  └────────────────────┘       │ │
│                                    └─────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │              Flask REST API  (app.py)                           ││
│  └─────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │           Vanilla JS Single-Page Frontend (templates/)          ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎯 **Tailored Question Sets** | Role-specific technical + behavioural questions |
| 📄 **Resume Parsing** | Auto-extracts skills, experience, and role from PDF/TXT |
| 🤖 **IBM Granite LLM** | Answer generation via IBM Watsonx.ai (IBM Cloud Lite) |
| 🔍 **RAG Retrieval** | ChromaDB vector store with curated knowledge base |
| 📊 **Answer Evaluation** | Score + model answer + improvement tips |
| 🗓️ **Study Roadmap** | Multi-week preparation plan tailored to timeline |
| 🔎 **Knowledge Search** | Instant keyword search across question database |
| 💻 **Web UI** | Full-featured, responsive single-page interface |

---

## 📁 Project Structure

```
AICTE-Interview Trainer Agent/
├── .env                        # ← Environment variables (IBM credentials)
├── app.py                      # Flask REST API (entry point)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── src/
│   ├── __init__.py
│   ├── config.py               # Config loader from .env
│   ├── agent.py                # Interview Trainer Agent orchestrator
│   ├── rag_pipeline.py         # ChromaDB + IBM Granite RAG pipeline
│   ├── resume_parser.py        # PDF/TXT resume parser
│   └── knowledge_base.py      # Static knowledge base (seed data)
│
├── templates/
│   └── index.html              # Frontend SPA
│
├── static/
│   ├── css/style.css           # UI styles (IBM design system inspired)
│   └── js/app.js               # Frontend logic
│
└── data/
    ├── chroma_db/              # Persistent ChromaDB vector store
    ├── uploads/                # Temporary resume uploads
    └── knowledge_base/         # Additional knowledge documents
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- IBM Cloud Lite account → [cloud.ibm.com](https://cloud.ibm.com)
- IBM Watsonx.ai project → [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com)

### Step 1 – Clone & Install

```bash
cd "AICTE-Interview Trainer Agent"
pip install -r requirements.txt
```

### Step 2 – Configure IBM Cloud Credentials

Edit the `.env` file and fill in your real values:

```env
IBM_WATSONX_API_KEY=<your-api-key>       # From: cloud.ibm.com/iam/apikeys
IBM_WATSONX_PROJECT_ID=<your-project-id> # From: dataplatform.cloud.ibm.com
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_GRANITE_MODEL_ID=ibm/granite-13b-chat-v2
```

> **Getting credentials:**
> 1. Go to [cloud.ibm.com](https://cloud.ibm.com) → Create a free **Lite** account
> 2. Create a **Watson Machine Learning** service instance (Lite plan)
> 3. Go to **Manage → API keys** → Create an API key
> 4. Open [dataplatform.cloud.ibm.com](https://dataplatform.cloud.ibm.com) → Create a project → Copy Project ID

### Step 3 – Run

```bash
python app.py
```

Open your browser at **http://localhost:5000**

---

## 🔌 REST API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check + model info |
| POST | `/api/prepare/profile` | Generate plan from manual profile |
| POST | `/api/prepare/resume` | Generate plan from uploaded resume |
| POST | `/api/evaluate` | Evaluate a candidate's answer |
| POST | `/api/strategy` | Generate study roadmap only |
| GET | `/api/questions/search?q=...` | Search knowledge base |
| GET | `/api/roles` | List supported job roles |
| GET | `/api/levels` | List experience levels |

### Example: Generate Plan from Profile

```bash
curl -X POST http://localhost:5000/api/prepare/profile \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Priya Patel",
    "job_role": "Data Scientist",
    "experience_level": "mid",
    "skills": ["Python", "pandas", "scikit-learn", "SQL"],
    "timeline_days": 21
  }'
```

### Example: Upload Resume

```bash
curl -X POST http://localhost:5000/api/prepare/resume \
  -F "file=@resume.pdf" \
  -F "timeline_days=30"
```

### Example: Evaluate Answer

```bash
curl -X POST http://localhost:5000/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "role": "Software Engineer",
    "question": "Explain the SOLID principles.",
    "candidate_answer": "SOLID stands for Single Responsibility..."
  }'
```

---

## 🤖 IBM Granite Models (Compatible with Lite Plan)

| Model ID | Best For |
|---|---|
| `ibm/granite-13b-chat-v2` | Default – conversational, detailed answers |
| `ibm/granite-3-8b-instruct` | Faster, lighter, good for most questions |
| `ibm/granite-20b-multilingual` | Multi-language support |

Change in `.env`:
```env
IBM_GRANITE_MODEL_ID=ibm/granite-3-8b-instruct
```

---

## 🧠 RAG Pipeline Details

1. **Knowledge Base Seeding**: On first run, 10+ curated documents covering Software Engineering, Data Science, DevOps, Product Management, HR questions, STAR method guide, and industry expectations are embedded and stored in **ChromaDB**.

2. **Embedding**: Uses `all-MiniLM-L6-v2` (SentenceTransformer) locally — no API cost.

3. **Retrieval**: For each query, top-k semantically similar documents are retrieved from ChromaDB with optional role-based filtering.

4. **Generation**: Retrieved context + candidate profile is injected into a structured prompt sent to **IBM Granite** via Watsonx.ai.

5. **Resume Indexing**: Uploaded resumes are parsed, embedded, and indexed into ChromaDB for personalised retrieval.

---

## 🎓 Supported Roles

- Software Engineer
- Data Scientist
- Frontend Developer
- Backend Developer
- Full Stack Developer
- DevOps Engineer
- Product Manager
- Data Analyst
- AI/ML Engineer
- Cybersecurity Analyst

---

## 📋 Technologies Used

| Technology | Purpose |
|---|---|
| **IBM Granite** (Watsonx.ai) | LLM for question/answer generation |
| **IBM Cloud Lite** | Free-tier cloud infrastructure |
| **LangChain** | LLM orchestration & prompt management |
| **ChromaDB** | Local vector store for RAG |
| **SentenceTransformers** | Text embeddings (local) |
| **Flask** | REST API server |
| **PyPDF2 / pdfminer** | Resume PDF parsing |
| **Vanilla JS** | Frontend (no framework needed) |

---
## Project Screenshots
![Interview Trainer Agent](images/WhatsApp Image 2026-11-06 at 12.50.57 PM)
![Interview Trainer Agent](images/WhatsApp Image 2026-11-06 at 12.50.57 PM (1))
![Interview Trainer Agent](images/WhatsApp Image 2026-11-06 at 12.50.58 PM)
![Interview Trainer Agent](WhatsApp Image 2026-11-06 at 12.50.58 PM (1))

## 👥 Team / AICTE Context

- **Problem Statement**: #22 – Interview Trainer Agent
- **Technology Mandate**: IBM Cloud Lite services / IBM Granite (mandatory)
- **Challenge**: RAG-powered agent that prepares users for job interviews by generating tailored question sets and preparation strategies

---

## 📄 License

MIT License — free for educational and personal use.
