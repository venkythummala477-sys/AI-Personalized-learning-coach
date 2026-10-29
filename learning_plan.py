
def format_plan_summary(plan):
    days = plan.get("days", [])

    total_minutes = sum(
        int(day.get("minutes", 0))
        for day in days
    )

    return {
        "title": plan.get("title", "Learning Plan"),
        "overview": plan.get("overview", ""),
        "day_count": len(days),
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 1)
    }


def get_topics(plan):
    return [
        day.get("topic", f"Day {day.get('day', index + 1)}")
        for index, day in enumerate(plan.get("days", []))
    ]


def get_day(plan, day_number):
    for day in plan.get("days", []):
        if int(day.get("day", 0)) == int(day_number):
            return day

    return None
