"""
rag_pipeline.py – RAG (Retrieval-Augmented Generation) pipeline.

Architecture:
  1. ChromaDB vector store seeded with the static interview knowledge base.
  2. SentenceTransformer embeddings (runs locally, no API cost).
  3. IBM Watsonx.ai / Granite LLM for answer generation.
  4. LangChain orchestration tying retrieval → prompt → generation.
"""

import os
import logging
from typing import Optional

# LangChain
from langchain_core.documents import Document
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

# IBM Watsonx LangChain integration
from langchain_ibm import WatsonxLLM

# Vector store
import chromadb
from chromadb.config import Settings as ChromaSettings

# Embeddings (local, no API needed for vectors)
from sentence_transformers import SentenceTransformer

from src.config import config
from src.knowledge_base import INTERVIEW_KNOWLEDGE_BASE

logger = logging.getLogger(__name__)

# ── Singleton state ──────────────────────────────────────────────────────────
_chroma_client: Optional[chromadb.Client] = None
_collection = None
_embedder: Optional[SentenceTransformer] = None
_llm: Optional[WatsonxLLM] = None


# ── Embedding helper ──────────────────────────────────────────────────────────

def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        logger.info("Loading SentenceTransformer model (all-MiniLM-L6-v2)…")
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _embed(texts: list[str]) -> list[list[float]]:
    embedder = _get_embedder()
    return embedder.encode(texts, convert_to_numpy=True).tolist()


# ── ChromaDB vector store ─────────────────────────────────────────────────────

def _get_chroma_collection():
    global _chroma_client, _collection
    if _collection is not None:
        return _collection

    os.makedirs(config.CHROMA_PERSIST_DIR, exist_ok=True)
    _chroma_client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    _collection = _chroma_client.get_or_create_collection(
        name=config.VECTOR_STORE_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(
        "ChromaDB collection '%s' ready (%d docs).",
        config.VECTOR_STORE_COLLECTION,
        _collection.count(),
    )
    return _collection


def seed_knowledge_base(force: bool = False) -> None:
    """Seed ChromaDB with the static interview knowledge base."""
    col = _get_chroma_collection()
    if col.count() > 0 and not force:
        logger.info("Knowledge base already seeded (%d docs). Skipping.", col.count())
        return

    logger.info("Seeding knowledge base with %d documents…", len(INTERVIEW_KNOWLEDGE_BASE))
    texts = [doc["content"] for doc in INTERVIEW_KNOWLEDGE_BASE]
    ids   = [doc["id"] for doc in INTERVIEW_KNOWLEDGE_BASE]
    metas = [
        {
            "role":     doc.get("role", "all"),
            "category": doc.get("category", "general"),
            "level":    doc.get("level", "all"),
        }
        for doc in INTERVIEW_KNOWLEDGE_BASE
    ]
    embeddings = _embed(texts)
    col.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metas)
    logger.info("Knowledge base seeded successfully.")


def add_resume_to_vectorstore(candidate_id: str, resume_text: str, metadata: dict) -> None:
    """Index a candidate's resume text into the vector store."""
    col = _get_chroma_collection()
    embeddings = _embed([resume_text])
    col.upsert(
        ids=[f"resume_{candidate_id}"],
        embeddings=embeddings,
        documents=[resume_text],
        metadatas=[{**metadata, "type": "resume"}],
    )
    logger.info("Resume indexed for candidate '%s'.", candidate_id)


def retrieve_relevant_docs(query: str, top_k: int = None, role_filter: str = None) -> list[str]:
    """
    Retrieve the top-k most relevant documents from the vector store.

    Args:
        query:       The search query string.
        top_k:       Number of documents to retrieve (defaults to config.RAG_TOP_K).
        role_filter: Optional role to narrow the search (e.g. 'Software Engineer').

    Returns:
        List of document content strings ordered by relevance.
    """
    col = _get_chroma_collection()
    k = top_k or config.RAG_TOP_K
    query_embedding = _embed([query])

    where_filter = None
    if role_filter and role_filter.lower() not in ("all", ""):
        where_filter = {
            "$or": [
                {"role": {"$eq": role_filter}},
                {"role": {"$eq": "all"}},
            ]
        }

    kwargs = dict(
        query_embeddings=query_embedding,
        n_results=min(k, max(col.count(), 1)),
        include=["documents"],
    )
    if where_filter:
        kwargs["where"] = where_filter

    results = col.query(**kwargs)
    return results["documents"][0] if results["documents"] else []


# ── IBM Watsonx / Granite LLM ─────────────────────────────────────────────────

def _get_llm() -> WatsonxLLM:
    global _llm
    if _llm is not None:
        return _llm

    logger.info("Initialising IBM Watsonx LLM (model=%s)…", config.IBM_GRANITE_MODEL_ID)
    _llm = WatsonxLLM(
        model_id=config.IBM_GRANITE_MODEL_ID,
        url=config.IBM_WATSONX_URL,
        apikey=config.IBM_WATSONX_API_KEY,
        project_id=config.IBM_WATSONX_PROJECT_ID,
        params={
            "max_new_tokens": config.MAX_TOKENS,
            "temperature":    config.TEMPERATURE,
            "top_p":          config.TOP_P,
            "decoding_method": "sample",
            "repetition_penalty": 1.1,
        },
    )
    return _llm


# ── Prompt templates ──────────────────────────────────────────────────────────

QUESTION_GENERATION_PROMPT = PromptTemplate(
    input_variables=["context", "name", "role", "level", "skills"],
    template="""You are an expert Interview Trainer AI powered by IBM Granite.
Use the retrieved context below to generate a highly tailored interview preparation plan.

Candidate Profile:
- Name: {name}
- Target Role: {role}
- Experience Level: {level}
- Key Skills: {skills}

Retrieved Knowledge Base Context:
{context}

Generate a comprehensive interview preparation response that includes:
1. **5 Technical Questions** specifically tailored to the role and skills (with model answers)
2. **3 Behavioural Questions** using the STAR method framework
3. **2 HR Questions** with guidance on ideal responses
4. **Preparation Strategy** (3–5 actionable tips for this specific role/level)
5. **Key Areas to Improve** based on the candidate profile

Be specific, practical, and encouraging. Format your response clearly with headers.
""",
)

FOLLOW_UP_PROMPT = PromptTemplate(
    input_variables=["context", "role", "question", "candidate_answer"],
    template="""You are an expert Interview Coach powered by IBM Granite.

Role: {role}
Interview Question: {question}
Candidate's Answer: {candidate_answer}

Retrieved coaching context:
{context}

Provide constructive feedback on the candidate's answer including:
1. **Strengths** – What was good about the answer
2. **Areas for Improvement** – Specific weaknesses to address
3. **Model Answer** – A stronger version of the answer
4. **Score** – Rate the answer 1-10 with brief justification

Be specific and encouraging.
""",
)

STRATEGY_PROMPT = PromptTemplate(
    input_variables=["context", "role", "level", "skills", "timeline_days"],
    template="""You are an expert Interview Strategist powered by IBM Granite.

Target Role: {role}
Experience Level: {level}
Skills: {skills}
Preparation Timeline: {timeline_days} days

Retrieved industry context:
{context}

Create a detailed {timeline_days}-day interview preparation roadmap including:
1. **Daily Study Plan** – What to focus on each day/week
2. **Resources** – Specific topics, platforms, and practice methods
3. **Mock Interview Schedule** – When to practice and how
4. **Technical Topics** – Priority areas to master
5. **Soft Skills** – Behavioural preparation activities
6. **Company Research** – How to research the target company
7. **Final Week Checklist** – Last-minute preparation steps

Make the plan realistic and actionable.
""",
)


# ── Core generation functions ─────────────────────────────────────────────────

def generate_interview_questions(
    name: str,
    role: str,
    level: str,
    skills: list[str],
) -> str:
    """
    Generate a full tailored interview preparation plan using RAG + IBM Granite.

    Returns the LLM-generated markdown response string.
    """
    query = f"interview questions for {role} {level} level {' '.join(skills[:5])}"
    docs = retrieve_relevant_docs(query, role_filter=role)
    context = "\n\n---\n\n".join(docs) if docs else "No specific context available."

    llm = _get_llm()
    prompt_text = QUESTION_GENERATION_PROMPT.format(
        context=context,
        name=name,
        role=role,
        level=level,
        skills=", ".join(skills) if skills else "General",
    )
    logger.info("Generating interview questions for %s (%s / %s)…", name, role, level)
    response = llm.invoke(prompt_text)
    return response


def evaluate_answer(role: str, question: str, candidate_answer: str) -> str:
    """
    Evaluate a candidate's answer and provide structured feedback via IBM Granite.
    """
    query = f"model answer evaluation feedback for {role} interview question"
    docs  = retrieve_relevant_docs(query, role_filter=role)
    context = "\n\n---\n\n".join(docs) if docs else "No specific context available."

    llm = _get_llm()
    prompt_text = FOLLOW_UP_PROMPT.format(
        context=context,
        role=role,
        question=question,
        candidate_answer=candidate_answer,
    )
    logger.info("Evaluating answer for role '%s'…", role)
    return llm.invoke(prompt_text)


def generate_preparation_strategy(
    role: str,
    level: str,
    skills: list[str],
    timeline_days: int = 30,
) -> str:
    """
    Generate a multi-week interview preparation roadmap using IBM Granite.
    """
    query = f"interview preparation strategy roadmap {role} {level}"
    docs  = retrieve_relevant_docs(query, role_filter=role)
    context = "\n\n---\n\n".join(docs) if docs else "No specific context available."

    llm = _get_llm()
    prompt_text = STRATEGY_PROMPT.format(
        context=context,
        role=role,
        level=level,
        skills=", ".join(skills) if skills else "General",
        timeline_days=timeline_days,
    )
    logger.info("Generating %d-day strategy for '%s' (%s)…", timeline_days, role, level)
    return llm.invoke(prompt_text)
