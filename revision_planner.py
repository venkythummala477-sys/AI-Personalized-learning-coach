
from ai_service import generate_revision_advice


def create_revision_plan(subject, weak_topics):
    advice = generate_revision_advice(
        subject,
        weak_topics
    )

    return {
        "status": "revise" if weak_topics else "strong",
        "message": (
            "Revise the topics listed below."
            if weak_topics
            else "Great work! Move to the next topic."
        ),
        "steps": [
            line.strip(" -•\t")
            for line in advice.splitlines()
            if line.strip()
        ]
    }
