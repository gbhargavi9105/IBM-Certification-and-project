"""
Mental Health Awareness & Suicide Prevention Agent
Main Flask Application
Powered by Groq API + Agentic AI Architecture
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any

from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from local config.env
# config.env is intentionally excluded from GitHub using .gitignore
load_dotenv("config.env")

# ─── Agent imports ─────────────────────────────────────────────────────────────
from agents.crisis_detector import CrisisDetector, CrisisLevel
from agents.empathy_engine import EmpathyEngine
from agents.resource_agent import ResourceAgent
from agents.wellness_agent import ProactiveWellnessAgent

# ─── App setup ────────────────────────────────────────────────────────────────
app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "mh_secure_key_default"
)

CORS(app, supports_credentials=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# ─── Groq client ─────────────────────────────────────────────────────────────
# IMPORTANT:
# The API key is loaded ONLY from the local environment/config.env.
# Never hard-code API keys in source code.
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not set. "
        "Please add GROQ_API_KEY to your local config.env file."
    )

groq_client = Groq(api_key=GROQ_API_KEY)

GROQ_MODEL = "groq/compound"

# ─── Agent instances ──────────────────────────────────────────────────────────
crisis_detector = CrisisDetector()
empathy_engine = EmpathyEngine()
resource_agent = ResourceAgent()
wellness_agent = ProactiveWellnessAgent()

# ─── In-memory session store ──────────────────────────────────────────────────
# session_id -> {
#     "history": [...],
#     "message_count": int,
#     "risk_log": [...]
# }
sessions: Dict[str, Dict] = {}


# ─── System prompt builder ────────────────────────────────────────────────────

def build_system_prompt(crisis_context: str, empathy_block: str) -> str:
    return f"""You are Serene — a compassionate, professional AI mental health companion and suicide prevention support agent.

IDENTITY & MISSION:
- You provide empathetic, non-judgmental emotional support for people experiencing mental health challenges.
- You are trained in evidence-based supportive listening techniques: active listening, validation, motivational interviewing, and safety planning principles.
- You are NOT a replacement for professional mental health care. You always encourage professional support when appropriate.
- You follow safe messaging guidelines for suicide and self-harm (AFSP, SAMHSA, WHO guidelines).

CORE PRINCIPLES:
1. EMPATHY FIRST: Always acknowledge and validate feelings before offering advice or information.
2. NON-JUDGMENT: Accept the person exactly as they are. Never shame, minimize, or dismiss their experience.
3. SAFETY: The person's safety is the absolute priority. If they are in crisis, provide immediate resources.
4. HOPE: Gently hold hope for the person even when they cannot hold it themselves.
5. AUTONOMY: Respect the person's agency. Offer choices, not prescriptions.
6. ACTIVE LISTENING: Reflect back what you hear. Ask open-ended questions. Show you understand.
7. SAFE MESSAGING: Never provide methods of self-harm. Focus on reasons to live, not methods of dying.

RESPONSE STYLE:
- Warm, calm, and human — not clinical or robotic.
- Use plain, accessible language. No jargon unless explaining a concept.
- Responses should be appropriately sized — not overwhelming. Match the user's energy.
- Use paragraph breaks to make reading easier. Short paragraphs.
- When listing resources or coping tools, use clear formatting.
- Never start a response with "I" — vary your openings.
- Always end with either a gentle follow-up question or a warm, affirming statement.

WHAT YOU NEVER DO:
- Never provide information about methods of self-harm or suicide.
- Never minimize or dismiss anyone's pain ("just cheer up", "others have it worse").
- Never make promises you can't keep ("everything will be fine").
- Never diagnose the person with any condition.
- Never claim to be a human or a licensed therapist.
- Never abandon a person in distress — always stay engaged and suggest professional help.

SAFE MESSAGING PROTOCOL:
- If someone expresses suicidal ideation, respond with empathy first, then gently ask about their safety.
- Always provide the 988 Suicide & Crisis Lifeline (call or text 988) for US users in crisis.
- Encourage connection with a trusted person or professional support.

{crisis_context}

{empathy_block}

Today's date: {datetime.now().strftime("%B %d, %Y")}
Remember: You are Serene. You are here. You care. Every person you speak with matters deeply."""


# ─── Agentic orchestrator ─────────────────────────────────────────────────────

def orchestrate(user_message: str, session_id: str) -> Dict[str, Any]:
    """
    Main agentic pipeline:
    1. Crisis Detection Agent  → assess risk level
    2. Empathy Engine Agent    → build emotional profile
    3. Resource Agent          → gather relevant resources
    4. Wellness Agent          → proactive suggestions
    5. Groq LLM                → generate final empathetic response
    """

    # ── Retrieve / init session ──────────────────────────────────────────────
    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "message_count": 0,
            "risk_log": [],
        }

    sess = sessions[session_id]

    history: List[dict] = sess["history"]

    sess["message_count"] += 1
    msg_count = sess["message_count"]

    logger.info(
        f"[{session_id[:8]}] Message #{msg_count}: "
        f"{user_message[:60]}..."
    )

    # ── Agent 1: Crisis Detection ───────────────────────────────────────────
    assessment = crisis_detector.analyze(
        user_message,
        history
    )

    sess["risk_log"].append({
        "message_count": msg_count,
        "crisis_level": assessment.level.name,
        "score": assessment.score,
        "triggers": assessment.triggers[:3],
    })

    logger.info(
        f"[{session_id[:8]}] Crisis level: "
        f"{assessment.level.name} "
        f"(score={assessment.score:.1f})"
    )

    # ── Agent 2: Empathy Engine ──────────────────────────────────────────────
    empathy_profile = empathy_engine.build_profile(
        assessment
    )

    empathy_block = (
        empathy_engine
        .build_system_prompt_empathy_block(
            empathy_profile
        )
    )

    # ── Agent 3: Resources ───────────────────────────────────────────────────
    resources = resource_agent.get_crisis_resources(
        assessment.level
    )

    # ── Agent 4: Proactive Wellness ──────────────────────────────────────────
    wellness_insight = wellness_agent.analyze_and_suggest(
        user_message,
        msg_count
    )

    psychoeducation = wellness_agent.get_psychoeducation(
        user_message
    )

    # ── Inject crisis context into system prompt ─────────────────────────────
    crisis_context = (
        crisis_detector
        .get_crisis_context_prompt(assessment)
    )

    system_prompt = build_system_prompt(
        crisis_context,
        empathy_block
    )

    # ── Build messages for Groq ──────────────────────────────────────────────
    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    # Include recent conversation history
    # Last 12 turns to stay within context
    for msg in history[-12:]:
        messages.append(msg)

    # Add wellness/proactive context if relevant
    if (
        wellness_insight.check_in_message
        and msg_count % 6 == 0
    ):
        messages.append({
            "role": "system",
            "content": (
                "[PROACTIVE NUDGE] Consider naturally "
                f"weaving in a check-in: "
                f"'{wellness_insight.check_in_message}'"
            ),
        })

    # Current user message
    messages.append({
        "role": "user",
        "content": user_message
    })

    # ── Call Groq LLM ────────────────────────────────────────────────────────
    try:
        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.75,
            max_tokens=1024,
            top_p=0.9,
            stream=False,
        )

        ai_response = (
            completion
            .choices[0]
            .message
            .content
        )

    except Exception as e:
        logger.error(f"Groq API error: {e}")

        ai_response = (
            "I'm so sorry — I'm having a small technical "
            "difficulty right now. But please know, if "
            "you're in crisis, you can reach the 988 "
            "Suicide & Crisis Lifeline by calling or "
            "texting **988** — they're available 24/7 "
            "and completely free."
        )

    # ── Update conversation history ──────────────────────────────────────────
    history.append({
        "role": "user",
        "content": user_message
    })

    history.append({
        "role": "assistant",
        "content": ai_response
    })

    # Keep history manageable
    # Last 20 messages
    if len(history) > 20:
        sess["history"] = history[-20:]

    # ── Build structured response ────────────────────────────────────────────
    response_data = {
        "response": ai_response,
        "crisis_level": assessment.level.name,
        "crisis_score": round(assessment.score, 1),
        "show_resources": assessment.safety_resources_needed,
        "requires_immediate_action": (
            assessment.requires_immediate_action
        ),
        "resources": (
            resources
            if assessment.safety_resources_needed
            else None
        ),
        "affirmation": wellness_insight.affirmation,
        "psychoeducation": psychoeducation,
        "message_count": msg_count,
        "timestamp": datetime.now().isoformat(),
    }

    # For CRITICAL/HIGH, always append hotlines visibly
    if assessment.level in (
        CrisisLevel.CRITICAL,
        CrisisLevel.HIGH
    ):
        response_data["emergency_banner"] = True

        response_data["emergency_text"] = (
            "🆘 If you are in immediate danger, "
            "please call 988 (Suicide & Crisis Lifeline) "
            "or text HOME to 741741 right now. "
            "You can also call 911 or go to your nearest "
            "emergency room."
        )

    logger.info(
        f"[{session_id[:8]}] Response generated. "
        f"Crisis={assessment.level.name}"
    )

    return response_data


# ─── Flask routes ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    user_message = data.get(
        "message",
        ""
    ).strip()

    session_id = (
        data.get("session_id")
        or str(uuid.uuid4())
    )

    if not user_message:
        return jsonify({
            "error": "Message cannot be empty."
        }), 400

    if len(user_message) > 2000:
        return jsonify({
            "error": (
                "Message is too long "
                "(max 2000 characters)."
            )
        }), 400

    result = orchestrate(
        user_message,
        session_id
    )

    result["session_id"] = session_id

    return jsonify(result)


@app.route("/api/session/new", methods=["POST"])
def new_session():
    session_id = str(uuid.uuid4())

    sessions[session_id] = {
        "history": [],
        "message_count": 0,
        "risk_log": [],
        "created_at": datetime.now().isoformat(),
    }

    return jsonify({
        "session_id": session_id
    })


@app.route(
    "/api/session/<session_id>/history",
    methods=["GET"]
)
def get_history(session_id):
    if session_id not in sessions:
        return jsonify({
            "error": "Session not found"
        }), 404

    sess = sessions[session_id]

    return jsonify({
        "history": sess.get(
            "history",
            []
        ),
        "message_count": sess.get(
            "message_count",
            0
        ),
    })


@app.route("/api/resources", methods=["GET"])
def get_resources():
    return jsonify({
        "hotlines": (
            resource_agent
            .get_all_hotlines_formatted()
        ),
        "message": (
            "These resources are always "
            "available to you."
        ),
    })


@app.route(
    "/api/breathing-exercise",
    methods=["GET"]
)
def breathing_exercise():
    return jsonify({
        "exercise": "Box Breathing",

        "steps": [
            {
                "phase": "Inhale",
                "duration": 4,
                "instruction": (
                    "Breathe in slowly "
                    "through your nose"
                ),
            },
            {
                "phase": "Hold",
                "duration": 4,
                "instruction": (
                    "Hold your breath gently"
                ),
            },
            {
                "phase": "Exhale",
                "duration": 4,
                "instruction": (
                    "Breathe out slowly "
                    "through your mouth"
                ),
            },
            {
                "phase": "Hold",
                "duration": 4,
                "instruction": (
                    "Hold before the next breath"
                ),
            },
        ],

        "cycles": 4,

        "description": (
            "Box breathing is a simple "
            "paced-breathing exercise that "
            "may help promote relaxation "
            "during stressful moments."
        ),
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "agent": (
            "Serene - Mental Health & "
            "Suicide Prevention Agent"
        ),
        "model": GROQ_MODEL,
        "timestamp": datetime.now().isoformat(),
    })


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info(
        "  Serene — Mental Health & "
        "Suicide Prevention Agent"
    )
    logger.info(
        "  Powered by Groq + Agentic AI"
    )
    logger.info(
        "  Starting server at "
        "http://127.0.0.1:5000"
    )
    logger.info("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=os.getenv(
            "FLASK_DEBUG",
            "True"
        ).lower() == "true",
    )