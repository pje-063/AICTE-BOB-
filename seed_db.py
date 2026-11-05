"""
seed_db.py – One-time script to seed the ChromaDB knowledge base.
Run this before starting the server if you want to pre-warm the vector store.

Usage:
    python seed_db.py
"""

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from src.rag_pipeline import seed_knowledge_base

if __name__ == "__main__":
    print("Seeding ChromaDB knowledge base…")
    seed_knowledge_base(force=True)
    print("Done! Knowledge base is ready.")
