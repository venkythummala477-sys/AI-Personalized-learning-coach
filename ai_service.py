
import os
import re
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def ask_groq(prompt):
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY missing. Check your .env file."
        )

    try:
        client = Groq(
            api_key=api_key,
            timeout=90.0,
            max_retries=1,
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful AI Personalized Learning Coach. "
                        "Give clear, simple and structured guidance. "
                        "Follow the requested JSON format exactly."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_completion_tokens=3000,
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("Groq returned an empty response.")

        return content.strip()

    except Exception as error:
        if "timeout" in str(error).lower():
            raise ValueError(
                "Groq request timed out. Check your internet "
                "connection and try again."
            ) from error
        raise


def extract_json(text):
    """Extract and parse a JSON object from an AI response."""
    text = text.strip()

    text = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"\s*```\s*$", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError(
            "No JSON object found in AI response. "
            f"Response: {text[:500]}"
        )

    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON returned by AI: {exc}. "
            f"Response: {text[:500]}"
        ) from exc


def generate_learning_plan(
    subject, goal, level, duration, daily_minutes
):
    duration = int(duration)
    daily_minutes = int(daily_minutes)

    if duration < 1:
        raise ValueError("Duration must be at least 1 day.")

    prompt = f"""
Create a personalized daily learning plan.

Subject: {subject}
Learning goal: {goal}
Current level: {level}
Duration: {duration} days
Daily study time: {daily_minutes} minutes

Return ONLY valid JSON in this structure:
{{
  "title": "Personalized Study Plan",
  "subject": "Subject name",
  "goal": "Learning goal",
  "days": [
    {{
      "day": 1,
      "topic": "Introduction to the subject",
      "minutes": {daily_minutes},
      "objectives": ["Understand the basic concepts"],
      "activities": ["Study concepts", "Practice examples"],
      "checkpoint": "Explain the topic in your own words"
    }}
  ]
}}

Requirements:
- Return exactly {duration} day entries.
- Number the days consecutively from 1 to {duration}.
- Every day must have a meaningful, non-empty topic.
- Include objectives, activities, and a checkpoint for every day.
- Make topics progressively suitable for the student's level.
- Keep each day's content concise to reduce response time.
- Use {daily_minutes} minutes for each day's study time.
- Return JSON only. Do not use Markdown or code fences.
"""

    result = ask_groq(prompt)
    data = extract_json(result)

    if not isinstance(data, dict):
        raise ValueError("The learning plan must be a JSON object.")

    days = data.get("days")

    if not isinstance(days, list) or not days:
        raise ValueError(
            "The AI returned no daily topics. Please try again."
        )

    if len(days) != duration:
        raise ValueError(
            f"Expected {duration} daily topics, but received "
            f"{len(days)}. Please generate the plan again."
        )

    for index, day in enumerate(days, start=1):
        if not isinstance(day, dict):
            raise ValueError(f"Invalid format for Day {index}.")

        topic = day.get("topic")
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError(f"Topic is missing for Day {index}.")

        day["day"] = index
        day["minutes"] = daily_minutes

        for field in ("objectives", "activities"):
            if not isinstance(day.get(field), list):
                day[field] = []

        if not isinstance(day.get("checkpoint"), str):
            day["checkpoint"] = "Review today's topic."

    return data


def generate_quiz(subject, topic, level):
    prompt = f"""
Create exactly 5 multiple-choice quiz questions.

Subject: {subject}
Topic: {topic}
Level: {level}

Return ONLY valid JSON using this structure:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": 0,
      "explanation": "Short explanation"
    }}
  ]
}}

Requirements:
- Exactly 5 questions.
- Exactly 4 options per question.
- answer must be an integer from 0 to 3.
- Each question must have an explanation.
- Return JSON only, without Markdown fences.
"""

    result = ask_groq(prompt)
    data = extract_json(result)

    if not isinstance(data, dict):
        raise ValueError("The quiz response must be a JSON object.")

    questions = data.get("questions")

    if not isinstance(questions, list) or len(questions) != 5:
        raise ValueError("The AI must return exactly 5 questions.")

    for question in questions:
        if not isinstance(question, dict):
            raise ValueError("A quiz question has an invalid format.")

        options = question.get("options")
        answer = question.get("answer")

        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(
                "Each quiz question must have 4 options."
            )

        if (
            not isinstance(answer, int)
            or isinstance(answer, bool)
            or answer not in range(4)
        ):
            raise ValueError(
                "Each answer must be an integer from 0 to 3."
            )

        if not question.get("question"):
            raise ValueError("A quiz question is missing its text.")

        if not question.get("explanation"):
            raise ValueError(
                "A quiz question is missing its explanation."
            )

    return questions


def generate_revision_advice(subject, weak_topics):
    prompt = f"""
You are a supportive learning coach.

Subject: {subject}
Topics the student needs to revise: {weak_topics}

Give practical revision advice, a short study schedule,
and tips to improve understanding.
Use simple language.
"""

    return ask_groq(prompt)
