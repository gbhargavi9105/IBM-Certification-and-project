"""
Empathy Engine Agent
Generates empathetic, context-aware response modifiers and
selects the right emotional tone for the AI's reply.
"""

from dataclasses import dataclass
from typing import List, Optional
from agents.crisis_detector import CrisisLevel, CrisisAssessment


@dataclass
class EmpathyProfile:
    tone: str
    warmth_level: str          # "gentle" | "warm" | "urgent_caring"
    validation_phrases: List[str]
    coping_suggestions: List[str]
    follow_up_questions: List[str]
    affirmations: List[str]


# ─── Tone libraries ───────────────────────────────────────────────────────────

VALIDATION_PHRASES = {
    "critical": [
        "I hear you, and I'm so glad you're talking to me right now.",
        "What you're feeling sounds incredibly painful — you don't have to face this alone.",
        "Your life matters deeply, and I want to help you get through this moment.",
        "Thank you for trusting me with this. That took real courage.",
    ],
    "high": [
        "It sounds like you're carrying an enormous amount of pain right now.",
        "I can hear how exhausted and overwhelmed you are, and that's completely valid.",
        "You're not alone in this — I'm here with you.",
        "What you're going through sounds incredibly hard, and your feelings are real.",
    ],
    "moderate": [
        "I can hear that things have been really difficult for you lately.",
        "Your feelings are completely valid — it makes sense that you feel this way.",
        "You don't have to pretend to be okay. I'm here to listen.",
        "It takes strength to acknowledge when we're struggling.",
    ],
    "low": [
        "I understand things feel tough right now.",
        "It sounds like you've been going through a lot.",
        "I'm here for you, and I'm listening.",
        "Thank you for sharing that with me.",
    ],
    "general": [
        "I'm here to support you.",
        "Please feel free to share whatever is on your mind.",
        "Your well-being matters.",
    ],
}

COPING_SUGGESTIONS = {
    "grounding": [
        "Try the 5-4-3-2-1 grounding technique: name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste.",
        "Place both feet flat on the floor, take three slow deep breaths, and notice the physical sensation.",
        "Hold something cold (ice, a cold drink) — the physical sensation can interrupt intense emotions.",
    ],
    "breathing": [
        "Try box breathing: inhale for 4 counts, hold 4, exhale 4, hold 4 — repeat 4 times.",
        "Place one hand on your chest, breathe slowly so only your belly moves. Do this for 2 minutes.",
        "The 4-7-8 technique: breathe in for 4 seconds, hold for 7, exhale slowly for 8.",
    ],
    "connection": [
        "Is there one person — a friend, family member, or anyone — you could reach out to right now?",
        "Even sending a simple 'I need some company' text to someone you trust can help.",
        "Consider calling a warmline (non-crisis peer support line) just to hear a caring voice.",
    ],
    "self_care": [
        "Have you had water and food today? Sometimes our body's basic needs affect how we feel.",
        "Even a 5-minute walk outside can shift your nervous system state.",
        "A warm shower or bath can be physically soothing when emotions feel overwhelming.",
    ],
    "professional": [
        "Speaking with a therapist or counselor can provide tools tailored specifically to you.",
        "Your primary care doctor can also be a first step toward getting mental health support.",
        "Many workplaces and schools offer free counseling sessions through EAP programs.",
    ],
}

FOLLOW_UP_QUESTIONS = {
    "safety": [
        "Are you safe right now?",
        "Is there anyone with you or nearby right now?",
        "Do you have access to anything that could hurt you?",
    ],
    "exploration": [
        "Can you tell me more about what's been happening?",
        "How long have you been feeling this way?",
        "What does a typical day look like for you right now?",
    ],
    "support": [
        "Do you have people in your life you can lean on?",
        "Have you spoken to anyone else about how you're feeling?",
        "Is there a professional (therapist, doctor) you're currently seeing?",
    ],
    "needs": [
        "What would feel most helpful right now — someone to listen, or some practical suggestions?",
        "What kind of support are you hoping for today?",
        "What would make this moment even slightly more manageable for you?",
    ],
}

AFFIRMATIONS = [
    "You are stronger than you know.",
    "Asking for help is one of the bravest things a person can do.",
    "Your feelings are valid, and you deserve support.",
    "You matter — to the people in your life and to the world.",
    "This moment, no matter how dark, will not last forever.",
    "You don't have to have everything figured out right now.",
    "Taking things one small step at a time is enough.",
    "Recovery isn't linear, and that's okay.",
]


class EmpathyEngine:
    def build_profile(self, assessment: CrisisAssessment) -> EmpathyProfile:
        level_key = assessment.level.name.lower()

        if assessment.level == CrisisLevel.CRITICAL:
            return EmpathyProfile(
                tone="urgent_caring",
                warmth_level="urgent_caring",
                validation_phrases=VALIDATION_PHRASES["critical"],
                coping_suggestions=COPING_SUGGESTIONS["grounding"] + COPING_SUGGESTIONS["breathing"],
                follow_up_questions=FOLLOW_UP_QUESTIONS["safety"],
                affirmations=AFFIRMATIONS[:3],
            )
        elif assessment.level == CrisisLevel.HIGH:
            return EmpathyProfile(
                tone="deeply_empathetic",
                warmth_level="warm",
                validation_phrases=VALIDATION_PHRASES["high"],
                coping_suggestions=COPING_SUGGESTIONS["grounding"] + COPING_SUGGESTIONS["connection"],
                follow_up_questions=FOLLOW_UP_QUESTIONS["safety"] + FOLLOW_UP_QUESTIONS["support"],
                affirmations=AFFIRMATIONS[:4],
            )
        elif assessment.level == CrisisLevel.MODERATE:
            return EmpathyProfile(
                tone="empathetic_supportive",
                warmth_level="warm",
                validation_phrases=VALIDATION_PHRASES["moderate"],
                coping_suggestions=COPING_SUGGESTIONS["breathing"] + COPING_SUGGESTIONS["self_care"] + COPING_SUGGESTIONS["professional"],
                follow_up_questions=FOLLOW_UP_QUESTIONS["exploration"] + FOLLOW_UP_QUESTIONS["needs"],
                affirmations=AFFIRMATIONS[3:6],
            )
        elif assessment.level == CrisisLevel.LOW:
            return EmpathyProfile(
                tone="warm_supportive",
                warmth_level="gentle",
                validation_phrases=VALIDATION_PHRASES["low"],
                coping_suggestions=COPING_SUGGESTIONS["self_care"] + COPING_SUGGESTIONS["breathing"],
                follow_up_questions=FOLLOW_UP_QUESTIONS["exploration"] + FOLLOW_UP_QUESTIONS["needs"],
                affirmations=AFFIRMATIONS[5:],
            )
        else:
            return EmpathyProfile(
                tone="friendly_supportive",
                warmth_level="gentle",
                validation_phrases=VALIDATION_PHRASES["general"],
                coping_suggestions=COPING_SUGGESTIONS["self_care"],
                follow_up_questions=FOLLOW_UP_QUESTIONS["needs"],
                affirmations=[AFFIRMATIONS[0]],
            )

    def build_system_prompt_empathy_block(self, profile: EmpathyProfile) -> str:
        return f"""
EMPATHY DIRECTIVES:
- Tone: {profile.tone}
- Warmth level: {profile.warmth_level}
- Always validate before advising. Never say "just" or "simply" — these minimize pain.
- Never say "I know how you feel" — say "I can only imagine" or "that sounds incredibly hard".
- Never offer unsolicited advice until you've first acknowledged and validated the emotion.
- Mirror the user's language gently to show you are truly listening.
- End responses with either a caring follow-up question or a warm closing statement.
- Use "I" statements to show personal engagement: "I'm here with you", "I care about what you're going through".
"""
