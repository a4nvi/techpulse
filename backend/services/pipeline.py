# Orchestrates the full trend pipeline: fetch -> embed -> cluster -> compare against past trend -> score momentum -> summarise.
# this is what /api/trends will eventually call. Each cluster becomes a trend card.

from datetime import date
from services.news_fetcher import fetch_tech_news
from services.clustering import cluster_articles
from services.trend_memory import find_similar_past_trend, store_trend
from services.momentum import record_and_score
from services.summarizer import summarize_cluster

def run_pipeline(max_articles: int =20) -> list[dict]:
  """Runs one full fetch cycle and returns a list of trend cards, each with:
    summary, why_it_matters, image, sources, momentum, similar_past_trend."""

  articles = fetch_tech_news(max_articles=max_articles)
  clusters = cluster_articles(articles)

  trend_cards =[]
  for cluster in clusters:
        # Step 6: LLM summary + why-it-matters (also gives us clean text to
        # compare/store, instead of using raw article titles for that).
        summary_data = summarize_cluster(cluster)
        if summary_data["failed"]:
            # Don't pollute trend memory/momentum with a failed summarization —
            # still show the card so the user knows something broke, but skip
            # everything downstream that depends on the summary text being real.
            trend_cards.append({
                "trend_id": None,
                "summary": summary_data["summary"],
                "why_it_matters": summary_data["why_it_matters"],
                "image": summary_data["image"],
                "sources": summary_data["sources"],
                "momentum": None,
                "similar_past_trend": None,
            })
            continue
        cluster_summary_text = summary_data["summary"]

        # Step 4: check trend memory BEFORE storing this cycle's version,
        # so a trend never matches against itself.
        similar_past_trend = find_similar_past_trend(cluster_summary_text)

        # Step 7 (partial): persist this cluster into trend memory, reusing
        # the past trend's id if we matched one, so momentum tracks the same
        # trend_id across cycles instead of spawning a new id every time.
        trend_id = similar_past_trend["trend_id"] if similar_past_trend else None
        trend_id = store_trend(cluster_summary_text, str(date.today()), trend_id=trend_id)

        # Step 5: momentum is scored off mention-count for this trend_id
        momentum = record_and_score(trend_id, mention_count=len(cluster))

        trend_cards.append({
          "trend_id": trend_id,
          "summary": summary_data["summary"],
          "why_it_matters": summary_data["why_it_matters"],
          "image": summary_data["image"],
          "sources": summary_data["sources"],
          "momentum": momentum,
          "similar_past_trend": similar_past_trend,
        })

  return trend_cards

if __name__ == "__main__":
    cards = run_pipeline(max_articles=15)
    print(f"Generated {len(cards)} trend cards\n")
    for card in cards:
        print(f"[{card['momentum']['status'].upper()}] {card['summary']}")
        print(f"  Why it matters: {card['why_it_matters']}")
        if card["similar_past_trend"]:
            print(f"  Resembles past trend: {card['similar_past_trend']['summary']} (similarity: {card['similar_past_trend']['similarity']})")
        print()




