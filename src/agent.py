"""
agent.py – Interview Trainer Agent orchestrator.

Ties together resume parsing, vector-store indexing, and RAG-based generation
to deliver a full interview preparation experience via a clean Python API.
"""

import uuid
import logging
import os
from typing import Optional

from src.config import config
from src.resume_parser import parse_resume
from src.rag_pipeline import (
    seed_knowledge_base,
    add_resume_to_vectorstore,
    generate_interview_questions,
    evaluate_answer,
    generate_preparation_strategy,
    retrieve_relevant_docs,
)

logger = logging.getLogger(__name__)


class InterviewTrainerAgent:
    """
    High-level agent that coordinates the entire interview preparation workflow.

    Usage:
        agent = InterviewTrainerAgent()
        agent.initialise()

        # From resume file
        plan = agent.prepare_from_resume("path/to/resume.pdf")

        # From manual input
        plan = agent.prepare_from_profile(
            name="Arjun Sharma",
            job_role="Data Scientist",
            experience_level="mid",
            skills=["python", "pandas", "machine learning"],
        )
    """

    def __init__(self) -> None:
        self._ready = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def initialise(self) -> None:
        """Seed the knowledge base and warm-up the LLM connection."""
        if self._ready:
            return
        logger.info("Initialising Interview Trainer Agent…")
        seed_knowledge_base()
        self._ready = True
        logger.info("Agent ready.")

    def _ensure_ready(self) -> None:
        if not self._ready:
            self.initialise()

    # ── Profile construction ──────────────────────────────────────────────────

    def _build_profile(
        self,
        name: str,
        job_role: str,
        experience_level: str,
        skills: list[str],
        resume_path: Optional[str] = None,
    ) -> dict:
        profile = {
            "candidate_id":    str(uuid.uuid4())[:8],
            "name":            name,
            "job_role":        job_role,
            "experience_level": experience_level,
            "skills":          skills,
        }
        if resume_path:
            parsed = parse_resume(resume_path)
            # Override with parsed values if not explicitly provided
            if name == "Candidate":
                profile["name"] = parsed["name"]
            if not skills:
                profile["skills"] = (
                    parsed["skills"]["technical"] + parsed["skills"]["soft"]
                )
            profile["education"] = parsed.get("education", [])
            profile["email"]     = parsed.get("email", "")

            # Index resume in vector store
            add_resume_to_vectorstore(
                candidate_id=profile["candidate_id"],
                resume_text=parsed["raw_text"],
                metadata={
                    "name":  profile["name"],
                    "role":  job_role,
                    "level": experience_level,
                },
            )
        return profile

    # ── Main workflows ────────────────────────────────────────────────────────

    def prepare_from_profile(
        self,
        name: str,
        job_role: str,
        experience_level: str,
        skills: list[str],
        include_strategy: bool = True,
        timeline_days: int = 30,
    ) -> dict:
        """
        Generate a complete interview prep plan from a manual profile.

        Returns:
            {
                profile, questions_and_answers, preparation_strategy, status
            }
        """
        self._ensure_ready()
        profile = self._build_profile(name, job_role, experience_level, skills)
        return self._generate_plan(profile, include_strategy, timeline_days)

    def prepare_from_resume(
        self,
        resume_path: str,
        job_role_override: Optional[str] = None,
        experience_level_override: Optional[str] = None,
        include_strategy: bool = True,
        timeline_days: int = 30,
    ) -> dict:
        """
        Parse a resume and generate a complete interview prep plan.

        Args:
            resume_path:              Path to the uploaded PDF/TXT resume.
            job_role_override:        Override the auto-detected job role.
            experience_level_override: Override the auto-detected experience level.

        Returns: Same structure as prepare_from_profile().
        """
        self._ensure_ready()
        parsed = parse_resume(resume_path)

        profile = self._build_profile(
            name=parsed["name"],
            job_role=job_role_override or parsed["job_role"],
            experience_level=experience_level_override or parsed["experience_level"],
            skills=parsed["skills"]["technical"] + parsed["skills"]["soft"],
            resume_path=resume_path,
        )
        return self._generate_plan(profile, include_strategy, timeline_days)

    def _generate_plan(
        self,
        profile: dict,
        include_strategy: bool,
        timeline_days: int,
    ) -> dict:
        """Core generation: questions + optional preparation strategy."""
        result: dict = {"profile": profile, "status": "success"}

        try:
            result["questions_and_answers"] = generate_interview_questions(
                name=profile["name"],
                role=profile["job_role"],
                level=profile["experience_level"],
                skills=profile["skills"],
            )
        except Exception as exc:
            logger.error("Question generation failed: %s", exc)
            result["questions_and_answers"] = (
                "Could not generate questions. Please check your IBM Watsonx credentials."
            )
            result["status"] = "partial"

        if include_strategy:
            try:
                result["preparation_strategy"] = generate_preparation_strategy(
                    role=profile["job_role"],
                    level=profile["experience_level"],
                    skills=profile["skills"],
                    timeline_days=timeline_days,
                )
            except Exception as exc:
                logger.error("Strategy generation failed: %s", exc)
                result["preparation_strategy"] = (
                    "Could not generate strategy. Please check your IBM Watsonx credentials."
                )
                result["status"] = "partial"

        return result

    # ── Answer evaluation ─────────────────────────────────────────────────────

    def evaluate_candidate_answer(
        self,
        role: str,
        question: str,
        candidate_answer: str,
    ) -> dict:
        """
        Evaluate a candidate's mock answer and return structured feedback.

        Returns:
            { feedback, status }
        """
        self._ensure_ready()
        try:
            feedback = evaluate_answer(
                role=role,
                question=question,
                candidate_answer=candidate_answer,
            )
            return {"feedback": feedback, "status": "success"}
        except Exception as exc:
            logger.error("Answer evaluation failed: %s", exc)
            return {
                "feedback": f"Evaluation failed: {exc}",
                "status": "error",
            }

    # ── Quick question search ─────────────────────────────────────────────────

    def search_questions(self, query: str, role: Optional[str] = None) -> list[str]:
        """
        Search the knowledge base for relevant questions/tips without LLM generation.
        Useful for quick lookups that don't need full generation.
        """
        self._ensure_ready()
        return retrieve_relevant_docs(query, role_filter=role)

    # ── Supported roles & levels ──────────────────────────────────────────────

    @staticmethod
    def supported_roles() -> list[str]:
        return [
            "Software Engineer",
            "Data Scientist",
            "Frontend Developer",
            "Backend Developer",
            "Full Stack Developer",
            "DevOps Engineer",
            "Product Manager",
            "Data Analyst",
            "AI/ML Engineer",
            "Cybersecurity Analyst",
            "Other",
        ]

    @staticmethod
    def supported_levels() -> list[str]:
        return ["entry", "mid", "senior"]
