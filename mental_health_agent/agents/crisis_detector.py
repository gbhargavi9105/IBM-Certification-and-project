"""
Crisis Detection Agent
Analyzes user messages for signs of distress, crisis, and suicidal ideation.
Uses a multi-level risk assessment approach.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


class CrisisLevel(Enum):
    NONE = 0
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class CrisisAssessment:
    level: CrisisLevel
    score: float
    triggers: List[str]
    requires_immediate_action: bool
    recommended_response_type: str
    safety_resources_needed: bool


# ─── Keyword banks ────────────────────────────────────────────────────────────

CRITICAL_KEYWORDS = [
    "want to die", "kill myself", "end my life", "suicide", "suicidal",
    "don't want to live", "no reason to live", "better off dead",
    "take my own life", "end it all", "can't go on", "not worth living",
    "planning to die", "goodbye forever", "final goodbye", "last day",
    "overdose", "hang myself", "jump off", "slit my wrists",
    "i want to disappear forever", "everyone would be better without me",
]

HIGH_RISK_KEYWORDS = [
    "hopeless", "helpless", "worthless", "burden to everyone", "no way out",
    "can't take it anymore", "nothing matters", "give up on life",
    "feeling empty", "nothing left", "nobody cares if i die",
    "want to hurt myself", "self harm", "cutting myself", "hurting myself",
    "trapped", "no future", "pointless life", "suffering too much",
]

MODERATE_RISK_KEYWORDS = [
    "depressed", "depression", "anxiety", "panic attack", "overwhelming sadness",
    "can't stop crying", "don't want to get up", "no motivation",
    "feeling numb", "disconnected", "alone", "isolated", "no friends",
    "hate myself", "self loathing", "low self esteem", "worthless",
    "insomnia", "can't sleep", "lost appetite", "no energy",
    "feeling like a failure", "nobody understands me",
]

LOW_RISK_KEYWORDS = [
    "stressed", "worried", "anxious", "sad", "upset", "frustrated",
    "overwhelmed", "tired", "exhausted", "unhappy", "struggling",
    "hard time", "difficult", "not okay", "not feeling well",
    "down", "blue", "low", "bad day",
]

POSITIVE_INDICATORS = [
    "getting better", "improving", "hopeful", "looking forward",
    "reached out", "seeking help", "therapy", "counseling", "support",
]


# ─── Core detector ────────────────────────────────────────────────────────────

class CrisisDetector:
    def __init__(self):
        self.conversation_history: List[dict] = []
        self.consecutive_distress_count = 0

    def analyze(self, message: str, history: List[dict] = None) -> CrisisAssessment:
        text = message.lower()
        triggers: List[str] = []
        score = 0.0

        # Critical keywords – immediate danger
        for kw in CRITICAL_KEYWORDS:
            if kw in text:
                score += 10
                triggers.append(f"CRITICAL: '{kw}'")

        # High-risk keywords
        for kw in HIGH_RISK_KEYWORDS:
            if kw in text:
                score += 5
                triggers.append(f"HIGH: '{kw}'")

        # Moderate keywords
        for kw in MODERATE_RISK_KEYWORDS:
            if kw in text:
                score += 2
                triggers.append(f"MODERATE: '{kw}'")

        # Low-risk keywords
        for kw in LOW_RISK_KEYWORDS:
            if kw in text:
                score += 0.5
                triggers.append(f"LOW: '{kw}'")

        # Positive indicators reduce score slightly
        for kw in POSITIVE_INDICATORS:
            if kw in text:
                score = max(0, score - 1)

        # Contextual pattern boosts (only when base distress is already present)
        if score > 3 and re.search(r"\b(i have a plan|i know how|tonight|already decided)\b", text):
            score += 6  # specificity of intent

        if re.search(r"\b(goodbye|farewell|final message|last time)\b", text):
            score += 5

        if re.search(r"\b(no one|nobody|completely alone|all alone)\b", text):
            score += 2

        # Escalation check across recent history
        if history:
            recent_scores = [
                self._quick_score(m["content"])
                for m in history[-4:]
                if m.get("role") == "user"
            ]
            if len(recent_scores) >= 2 and all(s > 1 for s in recent_scores):
                score += 3  # persistent distress

        # Determine level
        level = self._score_to_level(score)

        return CrisisAssessment(
            level=level,
            score=score,
            triggers=triggers,
            requires_immediate_action=level in (CrisisLevel.HIGH, CrisisLevel.CRITICAL),
            recommended_response_type=self._response_type(level),
            safety_resources_needed=level.value >= CrisisLevel.MODERATE.value,
        )

    def _quick_score(self, text: str) -> float:
        text = text.lower()
        s = 0.0
        for kw in CRITICAL_KEYWORDS:
            if kw in text:
                s += 10
        for kw in HIGH_RISK_KEYWORDS:
            if kw in text:
                s += 5
        for kw in MODERATE_RISK_KEYWORDS:
            if kw in text:
                s += 2
        for kw in LOW_RISK_KEYWORDS:
            if kw in text:
                s += 0.5
        return s

    def _score_to_level(self, score: float) -> CrisisLevel:
        if score >= 10:
            return CrisisLevel.CRITICAL
        if score >= 6:
            return CrisisLevel.HIGH
        if score >= 3:
            return CrisisLevel.MODERATE
        if score >= 1:
            return CrisisLevel.LOW
        return CrisisLevel.NONE

    def _response_type(self, level: CrisisLevel) -> str:
        return {
            CrisisLevel.NONE: "supportive_general",
            CrisisLevel.LOW: "empathetic_supportive",
            CrisisLevel.MODERATE: "active_listening_resources",
            CrisisLevel.HIGH: "crisis_intervention",
            CrisisLevel.CRITICAL: "immediate_crisis_response",
        }[level]

    def get_crisis_context_prompt(self, assessment: CrisisAssessment) -> str:
        """Returns an instruction snippet injected into the system prompt."""
        if assessment.level == CrisisLevel.CRITICAL:
            return (
                "CRITICAL CRISIS DETECTED. The user may be in immediate danger. "
                "Respond with extreme empathy and urgency. Immediately provide "
                "crisis hotline numbers (988 Suicide & Crisis Lifeline). "
                "Do NOT provide any information that could facilitate harm. "
                "Stay with them emotionally. Ask if they are safe right now. "
                "Encourage them to call emergency services if needed."
            )
        if assessment.level == CrisisLevel.HIGH:
            return (
                "HIGH RISK detected. The user is expressing serious distress. "
                "Show deep empathy, validate their feelings completely. "
                "Gently provide crisis resources. Ask open-ended safety questions. "
                "Do not minimize their pain. Help them identify one safe person."
            )
        if assessment.level == CrisisLevel.MODERATE:
            return (
                "MODERATE distress detected. Respond with warmth and active listening. "
                "Validate their emotions without judgment. "
                "Offer coping strategies and professional support resources. "
                "Check in on their support system."
            )
        if assessment.level == CrisisLevel.LOW:
            return (
                "User is experiencing some distress. Be warm, empathetic, and supportive. "
                "Acknowledge their feelings and gently explore what they need."
            )
        return ""
