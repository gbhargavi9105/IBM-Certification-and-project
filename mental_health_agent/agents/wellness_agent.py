"""
Proactive Wellness Agent
Monitors conversation patterns and proactively suggests check-ins,
wellness activities, and follow-up care.
"""

from dataclasses import dataclass
from typing import List, Optional
import random


@dataclass
class WellnessInsight:
    check_in_message: Optional[str]
    activity_suggestion: Optional[str]
    affirmation: Optional[str]
    topic_detected: str


WELLNESS_CHECK_INS = [
    "How are you feeling compared to when we started talking?",
    "Before we continue, I just want to check — how are you doing right now, in this moment?",
    "I want to pause and make sure you feel heard. What's your emotional temperature right now?",
    "You've shared a lot — that takes courage. How are you holding up?",
    "I care about how you're doing beyond just this conversation. What's one thing you need most today?",
]

MOOD_ACTIVITIES = {
    "anxious": [
        "Try placing both hands on your heart, closing your eyes, and taking 3 slow breaths.",
        "Write down your three biggest worries, then next to each one write: 'I can handle this.'",
        "Step outside for 5 minutes — fresh air and a change of scenery can genuinely help.",
    ],
    "sad": [
        "Put on one song that has ever made you feel something positive.",
        "Write a letter to your younger self — what would you tell them?",
        "Do one kind thing for yourself today, however small.",
    ],
    "overwhelmed": [
        "Write down everything on your mind, then pick just ONE thing to focus on right now.",
        "Set a timer for 10 minutes and do nothing but breathe and rest.",
        "Say out loud: 'I am doing the best I can, and that is enough.'",
    ],
    "lonely": [
        "Reach out to one person today — even a short message counts.",
        "Try visiting a public space (café, library, park) just to be around people.",
        "Write about a time you felt truly connected — hold onto that memory.",
    ],
    "hopeless": [
        "Write down one tiny thing that is still okay in your world right now.",
        "Think of one person who has ever been kind to you — hold that image.",
        "Remember: feelings are not facts. This feeling will shift.",
    ],
    "angry": [
        "Physical movement can release anger — try a brisk walk, punching a pillow, or dancing.",
        "Write an unsent letter to whoever or whatever you're angry at.",
        "Name exactly what you're feeling: 'I feel angry because...'",
    ],
    "general": [
        "Take three deep breaths and check in with your body — where are you holding tension?",
        "Do one small act of self-care today.",
        "You've been brave enough to talk about your feelings — that matters.",
    ],
}

MICRO_AFFIRMATIONS = [
    "You are not alone in this.",
    "Your feelings are valid.",
    "It's okay to ask for help.",
    "You matter more than you know.",
    "You are doing the best you can.",
    "This hard moment will pass.",
    "You deserve kindness — especially from yourself.",
    "Small steps still move you forward.",
    "Your story isn't over.",
    "Healing isn't linear, and that's okay.",
]

PSYCHOEDUCATION_SNIPPETS = {
    "depression": (
        "💡 **About Depression**: Depression is a medical condition, not a character flaw or weakness. "
        "It changes how the brain works. With the right support — therapy, sometimes medication, lifestyle changes — "
        "most people do get better. You don't have to white-knuckle it alone."
    ),
    "anxiety": (
        "💡 **About Anxiety**: Anxiety is your nervous system's alarm system misfiring. "
        "It feels very real and very scary, but it cannot hurt you. Grounding techniques and therapy "
        "(especially CBT) have strong evidence for helping. You can learn to manage it."
    ),
    "grief": (
        "💡 **About Grief**: Grief doesn't follow a set timeline or stages. It's messy and non-linear. "
        "There's no 'right way' to grieve. Being patient with yourself is one of the most important things you can do."
    ),
    "trauma": (
        "💡 **About Trauma**: Trauma responses — flashbacks, hypervigilance, numbness — are normal responses "
        "to abnormal events. EMDR and trauma-focused CBT are highly effective treatments. "
        "What happened to you was not your fault."
    ),
    "burnout": (
        "💡 **About Burnout**: Burnout is chronic stress that hasn't been adequately managed. "
        "Rest is not laziness — it's a biological necessity. Your worth is not tied to your productivity."
    ),
}


class ProactiveWellnessAgent:
    def __init__(self):
        self.message_count = 0
        self.last_check_in_at = 0

    def analyze_and_suggest(self, user_message: str, message_count: int) -> WellnessInsight:
        self.message_count = message_count
        topic = self._detect_topic(user_message)

        # Proactive check-in every 6 messages
        check_in = None
        if message_count > 0 and message_count % 6 == 0:
            check_in = random.choice(WELLNESS_CHECK_INS)

        activity = None
        if topic in MOOD_ACTIVITIES:
            activity = random.choice(MOOD_ACTIVITIES[topic])
        elif message_count % 4 == 0:
            activity = random.choice(MOOD_ACTIVITIES["general"])

        affirmation = random.choice(MICRO_AFFIRMATIONS) if message_count % 3 == 0 else None

        return WellnessInsight(
            check_in_message=check_in,
            activity_suggestion=activity,
            affirmation=affirmation,
            topic_detected=topic,
        )

    def get_psychoeducation(self, message: str) -> Optional[str]:
        msg_lower = message.lower()
        for key, snippet in PSYCHOEDUCATION_SNIPPETS.items():
            if key in msg_lower:
                return snippet
        return None

    def _detect_topic(self, message: str) -> str:
        msg = message.lower()
        if any(w in msg for w in ["anxious", "anxiety", "panic", "worried", "nervous"]):
            return "anxious"
        if any(w in msg for w in ["sad", "depressed", "depression", "cry", "hopeless", "empty"]):
            return "sad"
        if any(w in msg for w in ["overwhelmed", "too much", "can't cope", "breaking down"]):
            return "overwhelmed"
        if any(w in msg for w in ["alone", "lonely", "isolated", "no one"]):
            return "lonely"
        if any(w in msg for w in ["hopeless", "no point", "nothing matters"]):
            return "hopeless"
        if any(w in msg for w in ["angry", "anger", "furious", "rage"]):
            return "angry"
        return "general"
