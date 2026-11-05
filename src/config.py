"""
config.py – Centralised configuration loader for the Interview Trainer Agent.
Reads all values from the .env file and exposes them as a typed Config object.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── IBM Watsonx / Granite ─────────────────────────────────────────────────
    IBM_WATSONX_API_KEY: str   = os.getenv("IBM_WATSONX_API_KEY", "")
    IBM_WATSONX_PROJECT_ID: str = os.getenv("IBM_WATSONX_PROJECT_ID", "")
    IBM_WATSONX_URL: str       = os.getenv(
        "IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com"
    )
    IBM_GRANITE_MODEL_ID: str  = os.getenv(
        "IBM_GRANITE_MODEL_ID", "ibm/granite-4-h-small"
    )

    # ── IBM Cloud Object Storage (optional) ───────────────────────────────────
    IBM_COS_API_KEY: str      = os.getenv("IBM_COS_API_KEY", "")
    IBM_COS_INSTANCE_ID: str  = os.getenv("IBM_COS_INSTANCE_ID", "")
    IBM_COS_ENDPOINT: str     = os.getenv("IBM_COS_ENDPOINT", "")
    IBM_COS_BUCKET: str       = os.getenv("IBM_COS_BUCKET", "interview-trainer-resumes")

    # ── Flask ─────────────────────────────────────────────────────────────────
    FLASK_ENV: str        = os.getenv("FLASK_ENV", "development")
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret")
    FLASK_PORT: int       = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG: bool     = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # ── Vector Store / RAG ────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str        = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
    VECTOR_STORE_COLLECTION: str   = os.getenv(
        "VECTOR_STORE_COLLECTION", "interview_knowledge_base"
    )

    # ── Generation Parameters ─────────────────────────────────────────────────
    MAX_TOKENS: int   = int(os.getenv("MAX_TOKENS", "1024"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    TOP_P: float      = float(os.getenv("TOP_P", "0.95"))
    RAG_TOP_K: int    = int(os.getenv("RAG_TOP_K", "5"))

    # ── File Upload ───────────────────────────────────────────────────────────
    RESUME_UPLOAD_FOLDER: str  = os.getenv("RESUME_UPLOAD_FOLDER", "./data/uploads")
    MAX_RESUME_SIZE_MB: int    = int(os.getenv("MAX_RESUME_SIZE_MB", "10"))
    ALLOWED_EXTENSIONS: set    = {"pdf", "txt", "docx"}

    @classmethod
    def validate(cls) -> None:
        """Raise ValueError if mandatory credentials are missing."""
        missing = []
        if not cls.IBM_WATSONX_API_KEY or cls.IBM_WATSONX_API_KEY.startswith("your_"):
            missing.append("IBM_WATSONX_API_KEY")
        if not cls.IBM_WATSONX_PROJECT_ID or cls.IBM_WATSONX_PROJECT_ID.startswith("your_"):
            missing.append("IBM_WATSONX_PROJECT_ID")
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Please update your .env file."
            )


config = Config()
