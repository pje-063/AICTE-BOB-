"""
app.py – Flask REST API for the AICTE Interview Trainer Agent.

Endpoints:
  GET  /                         → Serve the frontend SPA
  GET  /api/health               → Health check
  POST /api/prepare/profile      → Generate plan from manual profile
  POST /api/prepare/resume       → Generate plan from uploaded resume
  POST /api/evaluate             → Evaluate a candidate's answer
  GET  /api/questions/search     → Search knowledge base
  GET  /api/roles                → List supported roles
  GET  /api/levels               → List experience levels
  POST /api/strategy             → Generate preparation strategy only
"""

import os
import uuid
import logging
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from src.config import config
from src.agent import InterviewTrainerAgent

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = config.FLASK_SECRET_KEY
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Agent (lazy-initialised on first request) ─────────────────────────────────
agent = InterviewTrainerAgent()

# ── Upload helpers ────────────────────────────────────────────────────────────
UPLOAD_FOLDER = Path(config.RESUME_UPLOAD_FOLDER)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
MAX_BYTES = config.MAX_RESUME_SIZE_MB * 1024 * 1024


def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


# ── Middleware ────────────────────────────────────────────────────────────────

@app.before_request
def _initialise_agent():
    """Ensure the agent is ready before handling any request."""
    agent.initialise()


# ── Static / SPA ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/static/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status":  "healthy",
        "model":   config.IBM_GRANITE_MODEL_ID,
        "version": "1.0.0",
        "message": "Interview Trainer Agent is running.",
    })


# ── Prepare from profile ──────────────────────────────────────────────────────

@app.route("/api/prepare/profile", methods=["POST"])
def prepare_profile():
    """
    Body (JSON):
      { name, job_role, experience_level, skills[], timeline_days? }
    """
    data = request.get_json(silent=True) or {}

    name     = (data.get("name") or "").strip()
    role     = (data.get("job_role") or "").strip()
    level    = (data.get("experience_level") or "mid").strip().lower()
    skills   = data.get("skills") or []
    timeline = int(data.get("timeline_days") or 30)

    if not name:
        return jsonify({"error": "name is required"}), 400
    if not role:
        return jsonify({"error": "job_role is required"}), 400
    if level not in agent.supported_levels():
        return jsonify({"error": f"experience_level must be one of {agent.supported_levels()}"}), 400

    result = agent.prepare_from_profile(
        name=name,
        job_role=role,
        experience_level=level,
        skills=skills,
        include_strategy=True,
        timeline_days=timeline,
    )
    return jsonify(result)


# ── Prepare from resume ────────────────────────────────────────────────────────

@app.route("/api/prepare/resume", methods=["POST"])
def prepare_resume():
    """
    Multipart form-data:
      file           – resume file (PDF / TXT)
      job_role       – optional override
      experience_level – optional override
      timeline_days  – optional (default 30)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    if not _allowed_file(file.filename):
        return jsonify({
            "error": f"Unsupported file type. Allowed: {config.ALLOWED_EXTENSIONS}"
        }), 400

    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_BYTES:
        return jsonify({"error": f"File too large. Max {config.MAX_RESUME_SIZE_MB} MB."}), 413

    # Save temporarily
    filename   = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    saved_path = UPLOAD_FOLDER / filename
    file.save(saved_path)

    try:
        result = agent.prepare_from_resume(
            resume_path=str(saved_path),
            job_role_override=request.form.get("job_role") or None,
            experience_level_override=request.form.get("experience_level") or None,
            include_strategy=True,
            timeline_days=int(request.form.get("timeline_days") or 30),
        )
    finally:
        try:
            os.remove(saved_path)
        except OSError:
            pass

    return jsonify(result)


# ── Evaluate answer ────────────────────────────────────────────────────────────

@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """
    Body (JSON):
      { role, question, candidate_answer }
    """
    data = request.get_json(silent=True) or {}

    role   = (data.get("role") or "").strip()
    q      = (data.get("question") or "").strip()
    answer = (data.get("candidate_answer") or "").strip()

    if not role:
        return jsonify({"error": "role is required"}), 400
    if not q:
        return jsonify({"error": "question is required"}), 400
    if not answer:
        return jsonify({"error": "candidate_answer is required"}), 400

    result = agent.evaluate_candidate_answer(role=role, question=q, candidate_answer=answer)
    return jsonify(result)


# ── Strategy only ──────────────────────────────────────────────────────────────

@app.route("/api/strategy", methods=["POST"])
def strategy():
    """
    Body (JSON):
      { job_role, experience_level, skills[], timeline_days? }
    """
    data     = request.get_json(silent=True) or {}
    role     = (data.get("job_role") or "").strip()
    level    = (data.get("experience_level") or "mid").strip().lower()
    skills   = data.get("skills") or []
    timeline = int(data.get("timeline_days") or 30)

    if not role:
        return jsonify({"error": "job_role is required"}), 400

    from src.rag_pipeline import generate_preparation_strategy
    try:
        plan = generate_preparation_strategy(
            role=role, level=level, skills=skills, timeline_days=timeline
        )
        return jsonify({"strategy": plan, "status": "success"})
    except Exception as exc:
        logger.error("Strategy endpoint error: %s", exc)
        return jsonify({"error": str(exc), "status": "error"}), 500


# ── Search knowledge base ──────────────────────────────────────────────────────

@app.route("/api/questions/search", methods=["GET"])
def search_questions():
    """
    Query params: q (required), role (optional)
    """
    query = request.args.get("q", "").strip()
    role  = request.args.get("role", "").strip() or None

    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    docs = agent.search_questions(query=query, role=role)
    return jsonify({"results": docs, "count": len(docs)})


# ── Meta endpoints ─────────────────────────────────────────────────────────────

@app.route("/api/roles", methods=["GET"])
def roles():
    return jsonify({"roles": agent.supported_roles()})


@app.route("/api/levels", methods=["GET"])
def levels():
    return jsonify({"levels": agent.supported_levels()})


# ── Error handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    logger.exception("Internal server error")
    return jsonify({"error": "Internal server error"}), 500


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG,
    )
