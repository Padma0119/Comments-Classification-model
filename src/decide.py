import json
from pathlib import Path

SEVERITY = {"publish": 0, "review": 1, "auto_hide": 2}
SHORT_WORDS = 3          # comments shorter than this are unreliable
SHORT_REVIEW_FRAC = 0.6  # short comment scoring >= 60% of T_review goes to a human

def load_thresholds(path):
    return json.loads(Path(path).read_text())

def decide(scores: dict, thr: dict, text: str = "") -> dict:
    results = []
    for label, s in scores.items():
        t = thr[label]
        if s >= t["hide"]:
            action = "auto_hide"
        elif s >= t["review"]:
            action = "review"
        else:
            action = "publish"
        # threats are never auto-hidden or auto-published: a human decides
        if label == "threat" and action == "auto_hide":
            action = "review"
        results.append((SEVERITY[action], s, label, action))

    _, s, label, action = max(results)

    # short comments: never auto-hide, and review borderline ones
    if len(text.split()) < SHORT_WORDS:
        if action == "auto_hide":
            action = "review"
        elif action == "publish" and s >= thr[label]["review"] * SHORT_REVIEW_FRAC:
            action = "review"

    return {"action": action, "label": label, "score": round(float(s), 4)}