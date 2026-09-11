"""
Resource Agent
Provides crisis hotlines, mental health resources, coping tools,
and self-help information based on context and crisis level.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from agents.crisis_detector import CrisisLevel


@dataclass
class Resource:
    name: str
    description: str
    contact: str
    available: str
    category: str


# ─── Crisis hotlines ──────────────────────────────────────────────────────────

CRISIS_HOTLINES = [
    Resource(
        name="988 Suicide & Crisis Lifeline",
        description="Free, confidential support for people in suicidal crisis or emotional distress.",
        contact="Call or text 988",
        available="24/7",
        category="crisis",
    ),
    Resource(
        name="Crisis Text Line",
        description="Free crisis counseling via text message.",
        contact="Text HOME to 741741",
        available="24/7",
        category="crisis",
    ),
    Resource(
        name="SAMHSA National Helpline",
        description="Free, confidential treatment referrals and information for mental health and substance use.",
        contact="1-800-662-4357",
        available="24/7",
        category="crisis",
    ),
    Resource(
        name="National Alliance on Mental Illness (NAMI) Helpline",
        description="Support, information, and referrals for mental health conditions.",
        contact="1-800-950-6264 | Text NAMI to 741741",
        available="Mon–Fri 10am–10pm ET",
        category="support",
    ),
    Resource(
        name="International Association for Suicide Prevention",
        description="Global directory of crisis centers.",
        contact="https://www.iasp.info/resources/Crisis_Centres/",
        available="Varies by location",
        category="crisis",
    ),
    Resource(
        name="Veterans Crisis Line",
        description="Connects veterans and service members in crisis with qualified responders.",
        contact="Call 988, press 1 | Text 838255",
        available="24/7",
        category="crisis",
    ),
    Resource(
        name="Trevor Project (LGBTQ+ Youth)",
        description="Crisis intervention and suicide prevention for LGBTQ+ young people.",
        contact="1-866-488-7386 | Text START to 678-678",
        available="24/7",
        category="crisis",
    ),
    Resource(
        name="Trans Lifeline",
        description="Peer support hotline by and for trans people.",
        contact="877-565-8860",
        available="24/7",
        category="crisis",
    ),
]

MENTAL_HEALTH_RESOURCES = [
    Resource(
        name="Psychology Today Therapist Finder",
        description="Find therapists, psychiatrists, and counselors near you.",
        contact="https://www.psychologytoday.com/us/therapists",
        available="Online resource",
        category="professional",
    ),
    Resource(
        name="Open Path Collective",
        description="Affordable in-office and online therapy sessions ($30–$80).",
        contact="https://openpathcollective.org",
        available="Online resource",
        category="professional",
    ),
    Resource(
        name="7 Cups",
        description="Free emotional support from trained listeners and online therapy.",
        contact="https://www.7cups.com",
        available="24/7 online",
        category="support",
    ),
    Resource(
        name="MindLine",
        description="Text-based mental health support community.",
        contact="https://mindline.com",
        available="Online",
        category="support",
    ),
    Resource(
        name="Headspace",
        description="Guided meditation and mindfulness app for stress and anxiety.",
        contact="https://www.headspace.com",
        available="App",
        category="self_help",
    ),
    Resource(
        name="Calm",
        description="Sleep, meditation, and relaxation app.",
        contact="https://www.calm.com",
        available="App",
        category="self_help",
    ),
    Resource(
        name="NAMI Mental Health Resources",
        description="Educational resources about mental health conditions.",
        contact="https://www.nami.org",
        available="Online",
        category="education",
    ),
]

COPING_TOOLS = {
    "anxiety": [
        "🌬️ **Box Breathing**: Inhale 4s → Hold 4s → Exhale 4s → Hold 4s. Repeat 4 times.",
        "🌿 **5-4-3-2-1 Grounding**: Name 5 things you see, 4 you feel, 3 you hear, 2 you smell, 1 you taste.",
        "💪 **Progressive Muscle Relaxation**: Tense each muscle group for 5 seconds, then release.",
        "🚶 **Mindful Walking**: Focus only on each step, the ground beneath your feet.",
    ],
    "depression": [
        "☀️ **Behavioral Activation**: Do one small enjoyable activity today, even for 10 minutes.",
        "📓 **Gratitude Journal**: Write 3 small things you noticed today — even tiny ones count.",
        "🤝 **Social Connection**: Send one text to someone you care about.",
        "🏃 **Movement**: Even a 10-minute walk releases mood-boosting endorphins.",
        "🌅 **Morning Routine**: A simple consistent routine can anchor your day.",
    ],
    "stress": [
        "📋 **Priority List**: Write down everything worrying you, then mark what you can control.",
        "⏱️ **Time-boxing**: Work on one thing for 25 minutes, then take a 5-minute break.",
        "🛁 **Self-Care Reset**: A warm bath/shower, tea, or a short rest can recharge you.",
        "📵 **Digital Detox**: Take 30–60 minutes away from screens.",
    ],
    "loneliness": [
        "💬 **Reach out**: Text one person something kind or a simple check-in.",
        "🐾 **Animal connection**: Spend time with a pet or visit an animal shelter.",
        "🌐 **Online communities**: Join a community around something you love.",
        "📚 **Volunteer**: Helping others is one of the most powerful antidotes to loneliness.",
    ],
    "grief": [
        "😢 **Allow the feelings**: Grief has no timeline. Crying and feeling sad is healthy and necessary.",
        "🕯️ **Create a ritual**: Light a candle, journal, or do something meaningful in honor of what you've lost.",
        "🤝 **Grief support group**: Connecting with others who understand can be profoundly healing.",
        "🧘 **Be gentle with yourself**: You don't have to 'be strong' — healing takes time.",
    ],
}


class ResourceAgent:
    def get_crisis_resources(self, level: CrisisLevel) -> Dict:
        if level in (CrisisLevel.CRITICAL, CrisisLevel.HIGH):
            hotlines = CRISIS_HOTLINES[:4]  # Most important first
            return {
                "hotlines": [self._resource_to_dict(r) for r in hotlines],
                "message": "⚠️ Please reach out to one of these free, confidential services right now:",
                "priority": "immediate",
            }
        elif level == CrisisLevel.MODERATE:
            hotlines = CRISIS_HOTLINES[:2]
            support = [r for r in MENTAL_HEALTH_RESOURCES if r.category in ("support", "professional")][:2]
            return {
                "hotlines": [self._resource_to_dict(r) for r in hotlines],
                "support": [self._resource_to_dict(r) for r in support],
                "message": "Here are some resources that may help:",
                "priority": "recommended",
            }
        else:
            support = [r for r in MENTAL_HEALTH_RESOURCES if r.category == "self_help"][:2]
            return {
                "support": [self._resource_to_dict(r) for r in support],
                "message": "Some helpful tools:",
                "priority": "optional",
            }

    def get_coping_tools(self, topic: str) -> List[str]:
        topic_lower = topic.lower()
        for key in COPING_TOOLS:
            if key in topic_lower:
                return COPING_TOOLS[key]
        # Default mix
        return COPING_TOOLS["anxiety"][:2] + COPING_TOOLS["stress"][:2]

    def get_all_hotlines_formatted(self) -> str:
        lines = ["📞 **Crisis & Support Hotlines:**\n"]
        for r in CRISIS_HOTLINES:
            lines.append(f"• **{r.name}** — {r.contact} ({r.available})")
        return "\n".join(lines)

    def _resource_to_dict(self, r: Resource) -> dict:
        return {
            "name": r.name,
            "description": r.description,
            "contact": r.contact,
            "available": r.available,
            "category": r.category,
        }
