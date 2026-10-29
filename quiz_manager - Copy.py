
def evaluate_quiz(questions, selected_answers):
    score = 0
    results = []

    for index, question in enumerate(questions):
        selected = (
            selected_answers[index]
            if index < len(selected_answers)
            else None
        )

        correct = int(question["answer"])
        is_correct = selected == correct

        if is_correct:
            score += 1

        results.append({
            "question": question["question"],
            "selected": selected,
            "correct": correct,
            "is_correct": is_correct,
            "options": question["options"],
            "explanation": question.get("explanation", "")
        })

    return {
        "score": score,
        "total": len(questions),
        "results": results
    }


def detect_weak_topics(topic, evaluation):
    if evaluation["score"] < evaluation["total"]:
        return [topic]

    return []
