# Momentum is pure rate-of-change math on mention-counts, fetch-cycle to
# fetch-cycle — NOT machine learning. Per spec, be explicit about that
# distinction in interviews.

# trend_id must be STABLE across fetch cycles for this to mean anything — see
# trend_memory.py's store_trend/find_similar_past_trend, which is what
# generates/reuses trend_id in the real pipeline (main.py, built later).

import json
from pathlib import Path
from datetime import datetime, timezone

STORAGE_PATH = Path(__file__).resolve().parent.parent / "storage" / "momentum_history.json"

RISING_THRESHOLD_PCT = 15.0    # % increase to count as "rising"
FALLING_THRESHOLD_PCT = -15.0  # % decrease to count as "falling"


def _load_history() -> dict:
    """Load mention-count history for all trends. Returns {} if file doesn't exist yet."""
    if not STORAGE_PATH.exists():
        return {}
    with open(STORAGE_PATH, "r") as f:
        return json.load(f)


def _save_history(history: dict) -> None:
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORAGE_PATH, "w") as f:
        json.dump(history, f, indent=2)


def record_and_score(trend_id: str, mention_count: int) -> dict:
    """
    Records this cycle's mention count for a trend, compares it against the
    last recorded cycle for that same trend_id, and returns a momentum tag.

    Returns:
        {
          "status": "rising" | "falling" | "steady" | "new",
          "change_pct": float | None,
          "previous_count": int | None,
          "current_count": int
        }
    """
    history = _load_history()
    now = datetime.now(timezone.utc).isoformat()

    past_entries = history.get(trend_id, [])

    if not past_entries:
        # First time we've ever seen this trend_id — nothing to compare against
        result = {
            "status": "new",
            "change_pct": None,
            "previous_count": None,
            "current_count": mention_count,
        }
    else:
        previous_count = past_entries[-1]["mention_count"]

        if previous_count == 0:
            change_pct = 100.0 if mention_count > 0 else 0.0
        else:
            change_pct = ((mention_count - previous_count) / previous_count) * 100

        if change_pct >= RISING_THRESHOLD_PCT:
            status = "rising"
        elif change_pct <= FALLING_THRESHOLD_PCT:
            status = "falling"
        else:
            status = "steady"

        result = {
            "status": status,
            "change_pct": round(change_pct, 1),
            "previous_count": previous_count,
            "current_count": mention_count,
        }

    # Append this cycle's reading, keep last 30 cycles per trend to avoid unbounded growth
    past_entries.append({"timestamp": now, "mention_count": mention_count})
    history[trend_id] = past_entries[-30:]
    _save_history(history)

    return result


if __name__ == "__main__":
    # Simulate 4 fetch cycles for the same trend
    print(record_and_score("gpt5-launch", 2))   # cycle 1: first time seen -> "new"
    print(record_and_score("gpt5-launch", 5))   # cycle 2: 2 -> 5 -> rising
    print(record_and_score("gpt5-launch", 5))   # cycle 3: 5 -> 5 -> steady
    print(record_and_score("gpt5-launch", 3))   # cycle 4: 5 -> 3 -> falling
