# Why JSON file, not a database? Your spec explicitly says "no need for a full vector DB at this scale" — a simple JSON file storing {summary, date, embedding} per trend is enough for now. SQLite is also fine per your spec, but JSON is simpler to start with and easy to swap later.

# find_similar_past_trend does a brute-force search — compares the new trend against every stored past trend and returns the single best match, only if it crosses the similarity threshold (0.70, slightly looser than clustering's 0.75, since we're comparing summaries across time, not near-duplicate articles).

# store_trend is what gets called after we generate a trend's LLM summary (Step 9, coming later) — for now we can test it directly with plain text.

import json
from pathlib import Path
from services.embeddings import get_embedding
from services.clustering import cosine_similarity

STORAGE_PATH = Path(__file__).resolve().parent.parent / "storage" / "trend_memory.json"


def _load_memory() -> list[dict]:
    """Load stored past trends from disk. Returns empty list if file doesn't exist yet."""
    if not STORAGE_PATH.exists():
        return []
    with open(STORAGE_PATH, "r") as f:
        return json.load(f)


def _save_memory(memory: list[dict]) -> None:
    """Save the full trend memory list back to disk."""
    STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STORAGE_PATH, "w") as f:
        json.dump(memory, f, indent=2)


def find_similar_past_trend(cluster_summary: str, threshold: float = 0.50) -> dict | None:
    """
    Given a new trend's summary text, search past stored trends for the most
    similar one. Returns the matching past trend dict, or None if nothing
    crosses the similarity threshold.
    """
    memory = _load_memory()
    if not memory:
        return None

    new_embedding = get_embedding(cluster_summary)

    best_match = None
    best_score = 0.0

    for past_trend in memory:
        score = cosine_similarity(new_embedding, past_trend["embedding"])
        if score > best_score:
            best_score = score
            best_match = past_trend

    if best_match and best_score >= threshold:
        return {"summary": best_match["summary"], "date": best_match["date"], "similarity": round(best_score, 3)}
    print(f"DEBUG best_score={best_score:.3f} (threshold={threshold})")
    return None


def store_trend(cluster_summary: str, date: str) -> None:
    """
    Save a new trend cluster's summary + embedding + date into memory,
    so future trends can be compared against it.
    """
    memory = _load_memory()
    memory.append({
        "summary": cluster_summary,
        "date": date,
        "embedding": get_embedding(cluster_summary),
    })
    _save_memory(memory)

if __name__ == "__main__":
    from datetime import date

    # Simulate storing a past trend
    store_trend("OpenAI launches GPT-4 with major reasoning improvements", str(date.today()))

    # Now search for something similar
    result = find_similar_past_trend("OpenAI releases a new advanced AI model")
    print("Match found:", result)

    result2 = find_similar_past_trend("Apple announces new iPhone camera features")
    print("Match found:", result2)
