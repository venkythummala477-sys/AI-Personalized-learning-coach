import streamlit as st
from dotenv import load_dotenv

import database
from ai_service import generate_learning_plan, generate_quiz
from learning_plan import format_plan_summary
from quiz_manager import evaluate_quiz, detect_weak_topics
from revision_planner import create_revision_plan

load_dotenv()
database.init_db()

st.set_page_config(
    page_title="AI Personalized Learning Coach",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI Personalized Learning Coach")
st.write(
    "Create a study plan, practise with quizzes, "
    "and track your progress."
)

# Sidebar: Learning goal
with st.sidebar:
    st.header("Your learning goal")

    subject = st.text_input(
        "Subject",
        placeholder="Python programming"
    )

    goal = st.text_area(
        "Learning goal",
        placeholder="What do you want to learn?"
    )

    level = st.selectbox(
        "Current level",
        ["Beginner", "Some basics", "Intermediate", "Advanced"]
    )

    duration = st.slider(
        "Duration in days", 3, 30, 7
    )

    daily_minutes = st.select_slider(
        "Daily study time",
        options=[15, 20, 30, 45, 60, 90, 120],
        value=30
    )

    generate = st.button(
        "Generate learning plan",
        type="primary"
    )

# Generate and save a new plan
if generate:
    if not subject.strip() or not goal.strip():
        st.warning("Enter both subject and learning goal.")
    else:
        try:
            with st.spinner("Creating your plan..."):
                plan = generate_learning_plan(
                    subject.strip(),
                    goal.strip(),
                    level,
                    duration,
                    daily_minutes
                )

                plan_id = database.save_plan(
                    subject.strip(),
                    goal.strip(),
                    level,
                    duration,
                    daily_minutes,
                    plan
                )

                st.session_state["plan"] = plan
                st.session_state["plan_id"] = plan_id
                st.session_state["subject"] = subject.strip()
                st.session_state["level"] = level

                # Clear old quiz data for the new plan
                for key in [
                    "questions",
                    "evaluation",
                    "quiz_topic",
                    "weak_topics"
                ]:
                    st.session_state.pop(key, None)

        except Exception as error:
            st.error(f"Could not create the plan: {error}")

# Load the latest saved plan when needed
if "plan" not in st.session_state:
    saved = database.list_plans(limit=1)

    if saved:
        latest = database.get_plan(saved[0]["id"])

        if latest:
            st.session_state["plan"] = latest["plan"]
            st.session_state["plan_id"] = latest["id"]
            st.session_state["subject"] = latest["subject"]
            st.session_state["level"] = latest["current_level"]

# Main tabs
tab1, tab2, tab3 = st.tabs([
    "📅 Study Plan",
    "🧠 Quiz",
    "📊 Progress"
])

# TAB 1: Study Plan
with tab1:
    plan = st.session_state.get("plan")

    if not plan:
        st.info("Generate a plan using the sidebar.")
    else:
        summary = format_plan_summary(plan)

        st.subheader(summary["title"])
        st.write(summary["overview"])

        col1, col2 = st.columns(2)
        col1.metric("Study days", summary["day_count"])
        col2.metric("Total hours", summary["total_hours"])

        for day in plan.get("days", []):
            with st.expander(
                f"Day {day['day']}: {day['topic']}"
            ):
                st.write(
                    f"**Study time:** {day['minutes']} minutes"
                )

                st.markdown("**Objectives**")
                for objective in day.get("objectives", []):
                    st.write(f"- {objective}")

                st.markdown("**Activities**")
                for activity in day.get("activities", []):
                    st.write(f"- {activity}")

                st.markdown("**Checkpoint**")
                st.write(day.get("checkpoint", ""))

# TAB 2: Quiz
with tab2:
    plan = st.session_state.get("plan")

    if not plan:
        st.info("Generate a learning plan first.")
    else:
        days = plan.get("days", [])

        # Handle plans that contain no daily topics
        if not days:
            st.warning(
                "This study plan has no daily topics. "
                "Please generate a new learning plan."
            )
        else:
            topic_labels = [
                f"Day {day['day']}: {day['topic']}"
                for day in days
            ]

            selected_label = st.selectbox(
                "Choose a topic",
                topic_labels,
                key="selected_quiz_topic"
            )

            # Check selection before looking up the day
            if selected_label is not None and selected_label in topic_labels:
                selected_index = topic_labels.index(selected_label)
                selected_day = days[selected_index]
                topic = selected_day["topic"]

                if st.button("Generate 5-question quiz"):
                    try:
                        with st.spinner("Generating questions..."):
                            questions = generate_quiz(
                                st.session_state["subject"],
                                topic,
                                st.session_state["level"]
                            )

                            st.session_state["questions"] = questions
                            st.session_state["quiz_topic"] = topic
                            st.session_state.pop("evaluation", None)
                            st.session_state.pop("weak_topics", None)

                    except Exception as error:
                        st.error(f"Could not generate quiz: {error}")

                questions = st.session_state.get("questions", [])

                if questions:
                    with st.form("learning_quiz"):
                        answers = []

                        for index, question in enumerate(questions):
                            st.markdown(
                                f"**Q{index + 1}. {question['question']}**"
                            )

                            options = question["options"]

                            choice = st.radio(
                                f"Select answer for question {index + 1}",
                                ["Choose an answer"] + options,
                                key=f"answer_{index}"
                            )

                            if choice in options:
                                answers.append(options.index(choice))
                            else:
                                answers.append(None)

                        submitted = st.form_submit_button("Submit answers")

                    if submitted:
                        if any(answer is None for answer in answers):
                            st.warning(
                                "Please answer all questions before submitting."
                            )
                        else:
                            try:
                                evaluation = evaluate_quiz(
                                    questions, answers
                                )

                                weak_topics = detect_weak_topics(
                                    st.session_state["quiz_topic"],
                                    evaluation
                                )

                                database.save_attempt(
                                    st.session_state["plan_id"],
                                    st.session_state["quiz_topic"],
                                    evaluation["score"],
                                    evaluation["total"],
                                    answers,
                                    weak_topics
                                )

                                st.session_state["evaluation"] = evaluation
                                st.session_state["weak_topics"] = weak_topics

                            except Exception as error:
                                st.error(f"Could not evaluate quiz: {error}")

                evaluation = st.session_state.get("evaluation")

                if evaluation:
                    st.subheader(
                        f"Your score: {evaluation['score']}/{evaluation['total']}"
                    )

                    score_percent = (
                        evaluation["score"] / evaluation["total"]
                        if evaluation["total"] else 0
                    )
                    st.progress(score_percent)

                    for index, result in enumerate(
                        evaluation["results"], start=1
                    ):
                        if result["is_correct"]:
                            st.success(f"Q{index}: Correct!")
                        else:
                            correct_option = result["options"][
                                result["correct"]
                            ]
                            st.error(
                                f"Q{index}: Correct answer: {correct_option}"
                            )

                        st.caption(result["explanation"])

                    weak_topics = st.session_state.get("weak_topics", [])

                    if weak_topics:
                        st.warning(
                            "Needs revision: " + ", ".join(weak_topics)
                        )

                        if st.button("Generate revision advice"):
                            try:
                                with st.spinner(
                                    "Preparing revision steps..."
                                ):
                                    revision = create_revision_plan(
                                        st.session_state["subject"],
                                        weak_topics
                                    )

                                st.markdown("**Revision steps**")

                                for step in revision["steps"]:
                                    st.write(f"- {step}")

                            except Exception as error:
                                st.error(
                                    f"Could not create revision advice: {error}"
                                )
                    else:
                        st.success("Excellent! All answers are correct.")

# TAB 3: Progress
with tab3:
    plan = st.session_state.get("plan")
    plan_id = st.session_state.get("plan_id")
    all_attempts = database.list_attempts()

    # Filter attempts for the current plan when plan IDs are available
    if all_attempts and any("plan_id" in a for a in all_attempts):
        attempts = [
            a for a in all_attempts
            if a.get("plan_id") == plan_id
        ]
    else:
        attempts = all_attempts

    if not plan:
        st.info("Generate a learning plan first.")
    else:
        days = plan.get("days", [])
        total_topics = len(days)

        # Calculate unique topics practiced through quizzes
        attempted_topics = {
            str(a.get("topic", "")).strip().casefold()
            for a in attempts
            if a.get("topic")
        }

        planned_topics = {
            str(day.get("topic", "")).strip().casefold()
            for day in days
            if day.get("topic")
        }

        practiced_count = len(attempted_topics & planned_topics)

        topic_progress = (
            (practiced_count / total_topics) * 100
            if total_topics > 0 else 0
        )

        pending_topics = max(total_topics - practiced_count, 0)

        # Calculate overall quiz accuracy using all questions
        total_correct = sum(
            max(0, int(a.get("score") or 0))
            for a in attempts
        )

        total_questions = sum(
            max(0, int(a.get("total") or 0))
            for a in attempts
        )

        quiz_accuracy = (
            (total_correct / total_questions) * 100
            if total_questions > 0 else 0
        )

        # Progress dashboard
        st.subheader("📊 Your Learning Progress")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Topics Practised",
            f"{practiced_count}/{total_topics}"
        )

        col2.metric(
            "Topics Pending",
            pending_topics
        )

        col3.metric(
            "Quiz Accuracy",
            f"{quiz_accuracy:.1f}%"
            if total_questions > 0 else "N/A"
        )

        st.markdown("### 📚 Study Plan Progress")
        st.progress(topic_progress / 100)
        st.write(
            f"{topic_progress:.1f}% — "
            f"{practiced_count} of {total_topics} topics "
            "practised through quizzes."
        )

        st.caption(
            "A topic counts as practised after at least one quiz attempt. "
            "This does not necessarily mean the topic is mastered."
        )

        st.markdown("### 🧠 Quiz Performance")
        if total_questions > 0:
            st.progress(quiz_accuracy / 100)
            st.write(
                f"Correct answers: {total_correct}/{total_questions}"
            )
        else:
            st.info(
                "Complete and submit a quiz to calculate your quiz accuracy."
            )

        # Topic-wise practice status
        st.markdown("### 📅 Topic-wise Status")

        for day in days:
            topic = str(day.get("topic", "")).strip()
            topic_key = topic.casefold()

            if topic_key in attempted_topics:
                st.success(f"Day {day.get('day')}: {topic} — Practised")
            else:
                st.info(f"Day {day.get('day')}: {topic} — Pending")

        # Quiz history
        st.markdown("### 📝 Quiz History")
        st.metric("Total Quiz Attempts", len(attempts))

        if attempts:
            for attempt in attempts:
                score = int(attempt.get("score") or 0)
                total = int(attempt.get("total") or 0)

                percentage = (
                    (score / total) * 100
                    if total > 0 else 0
                )

                st.write(
                    f"**{attempt.get('topic', 'Unknown topic')}** — "
                    f"{score}/{total} ({percentage:.1f}%)"
                )

                st.caption(attempt.get("created_at", ""))
        else:
            st.info("No quiz attempts yet. Start your first quiz!")

    