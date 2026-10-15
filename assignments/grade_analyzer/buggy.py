"""Grade analytics module for course score processing."""


def assign_letter(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def analyze_grades(scores, curve=0):
    if not scores:
        return {"average": 0.0, "passing_count": 0, "letter_grades": []}

    curved_scores = []
    for s in scores:
        # Step 1: Add curve bonus to raw test score
        # (BUG on line 22: Forgot to clamp curved score to max 100)
        curved = s + curve
        curved_scores.append(curved)

    # Step 2: Compute class statistics
    avg = round(sum(curved_scores) / len(curved_scores), 1)
    passing = sum(1 for s in curved_scores if s >= 60)
    letters = [assign_letter(s) for s in curved_scores]

    return {
        "average": avg,
        "passing_count": passing,
        "letter_grades": letters,
    }
