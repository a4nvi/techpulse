# One combined Claude API call per trend cluster — asks for both the summary
# and the "why it matters" blurb in a single request, returned as JSON. This
# is cheaper/simpler than two separate calls, at the cost of slightly less
# rigid separation between "compression" and "reasoning" as distinct calls.

import os
import json
import re

from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

MODEL = "llama-3.3-70b-versatile"

def _pick_representative_image(cluster: list[dict]) -> str | None:
    """
    Picks the first article in the cluster that actually has an image URL.
    GNews doesn't guarantee every article has one, so we fall back through
    the cluster instead of just grabbing cluster[0].
    """
    for article in cluster:
        if article.get("image"):
            return article["image"]
    return None

def _repair_json(text: str) -> str:
    """
    Fixes a common Llama-on-Groq formatting slip: a missing comma between
    JSON fields, where a closing quote is directly followed by a newline
    and the next field's opening quote.
    """
    return re.sub(r'"\s*\n\s*"', '",\n  "', text)

def summarize_cluster(cluster: list[dict]) -> dict:
    """
    Given a cluster of related articles (same trend, multiple sources),
    generates a short summary + why-it-matters blurb in one Claude call.

    Returns:
        {
          "summary": str,
          "why_it_matters": str,
          "image": str | None,
          "sources": [{"title": str, "url": str, "source": str}, ...]
        }
    """
    # Build a compact digest of the cluster's articles for the prompt
    article_digest = "\n\n".join(
        f"Source: {a['source']}\nTitle: {a['title']}\nDescription: {a.get('description', '')}"
        for a in cluster
    )

    prompt = f"""You are analyzing a cluster of news articles that all cover the same tech trend/story.

{article_digest}

Respond with ONLY a JSON object (no markdown fences, no preamble) in this exact format:
{{
  "summary": "A 1-2 sentence neutral summary of what happened, combining info across all sources.",
  "why_it_matters": "A 1-2 sentence explanation of the industry impact or significance — go beyond restating the news, explain WHY this matters."
}}"""

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.choices[0].message.content.strip()

    # Defensive parsing — strip markdown fences if groq adds them despite instructions
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()
    repaired = _repair_json(cleaned)
    try:
        parsed = json.loads(repaired)
    except json.JSONDecodeError:
        # First attempt failed even after repair — retry the API call once,
        # since this is usually a one-off formatting slip, not a systematic issue
        retry_response = client.chat.completions.create(
            model=MODEL,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        retry_text = retry_response.choices[0].message.content.strip()
        retry_cleaned = _repair_json(retry_text.replace("```json", "").replace("```", "").strip())
        try:
           parsed = json.loads(retry_cleaned)
        except json.JSONDecodeError:
            parsed = {
                "summary": "Summary unavailable due to a parsing error.",
                "why_it_matters": "Unable to generate at this time.",
                "failed": True,
            }
    return {
        "summary": parsed.get("summary", ""),
        "why_it_matters": parsed.get("why_it_matters", ""),
        "image": _pick_representative_image(cluster),
        "sources": [
            {"title": a["title"], "url": a["url"], "source": a["source"]}
            for a in cluster
        ],
        "failed": parsed.get("failed", False),
    }


if __name__ == "__main__":
    from services.news_fetcher import fetch_tech_news
    from services.clustering import cluster_articles

    articles = fetch_tech_news(max_articles=10)
    clusters = cluster_articles(articles)

    for i, cluster in enumerate(clusters):
        result = summarize_cluster(cluster)
        print(f"--- Trend {i+1} ---")
        print("Summary:", result["summary"])
        print("Why it matters:", result["why_it_matters"])
        print("Image:", result["image"])
        print("Sources:", [s["source"] for s in result["sources"]])
        print()
