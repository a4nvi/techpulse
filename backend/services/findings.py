# Tech Findings Feed — combines two sources into one merged feed, sorted by
# recency:
#   1. arXiv API -> academic AI/CS papers, tagged "Research"
#   2. GNews filtered by launch/breakthrough/unveils/announces -> industry
#      news, tagged "Industry"
#
# arXiv needs no API key. GNews reuses the same fetch_tech_news() function
# from news_fetcher.py, just with a different query focused on announcement-
# style keywords rather than the broader AI/startup/software query used for
# trend clustering.

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from services.news_fetcher import fetch_tech_news

ARXIV_BASE_URL = "https://export.arxiv.org/api/query"
ARXIV_NAMESPACE = "{http://www.w3.org/2005/Atom}"

# AI/CS categories per arXiv's classification scheme
ARXIV_CATEGORIES = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL"

INDUSTRY_KEYWORDS_QUERY = "(launch OR launches OR unveils OR announces OR debuts) AND (AI OR software OR startup OR chip OR company)"

# Titles containing these are almost never genuine product/industry announcements —
# they're sales posts, opinion pieces, or listicles that happen to contain our
# keywords incidentally.
EXCLUDE_TITLE_PATTERNS = [
    "deal", "deals", "under $", "% off", "discount", "sale",
    "vs", "review", "why my", "still better", "best ",
]


def _is_genuine_announcement(title: str) -> bool:
    """
    Filters out deals/opinion/listicle content that matched our GNews query
    incidentally (e.g. 'Deals: the Galaxy S26 is under $1,000' contains no
    launch keyword but could still slip through broader queries; this is a
    safety net as the query itself gets refined further).
    """
    title_lower = title.lower()
    return not any(pattern in title_lower for pattern in EXCLUDE_TITLE_PATTERNS)

def fetch_arxiv_papers(max_results: int = 10) -> list[dict]:
    """
    Fetches recent AI/CS papers from arXiv, sorted by submission date
    (newest first). No API key required.
    """
    params = {
        "search_query": ARXIV_CATEGORIES,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }

    response = requests.get(ARXIV_BASE_URL, params=params)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    entries = root.findall(f"{ARXIV_NAMESPACE}entry")

    papers = []
    for entry in entries:
        title = entry.find(f"{ARXIV_NAMESPACE}title").text.strip().replace("\n", " ")
        summary = entry.find(f"{ARXIV_NAMESPACE}summary").text.strip().replace("\n", " ")
        url = entry.find(f"{ARXIV_NAMESPACE}id").text.strip()
        published = entry.find(f"{ARXIV_NAMESPACE}published").text.strip()

        papers.append({
            "title": title,
            "description": summary[:300] + ("..." if len(summary) > 300 else ""),
            "url": url,
            "published_at": published,
            "source": "arXiv",
            "image": None,  # arXiv doesn't provide article images
            "tag": "Research",
        })

    return papers


def fetch_industry_news(max_articles: int = 10) -> list[dict]:
    """
    Fetches industry/product announcement news via GNews, filtered toward
    launch/unveils/announces/debuts keywords scoped to tech, tagged "Industry".
    Over-fetches slightly since some results get filtered out client-side.
    """
    # Fetch extra since _is_genuine_announcement will drop some results
    articles = fetch_tech_news(max_articles=max_articles * 2, query=INDUSTRY_KEYWORDS_QUERY)

    filtered = [a for a in articles if _is_genuine_announcement(a["title"])]

    return [
        {
            "title": a["title"],
            "description": a.get("description", ""),
            "url": a["url"],
            "published_at": a["published_at"],
            "source": a["source"],
            "image": a.get("image"),
            "tag": "Industry",
        }
        for a in filtered[:max_articles]
    ]


def _parse_date_safe(date_str: str) -> datetime:
    """
    Normalizes date parsing across arXiv's format (2026-07-13T10:00:00Z) and
    GNews's format (2026-07-13T10:00:00Z) — they're actually the same ISO
    format, but this wrapper guards against a malformed date breaking the
    sort instead of crashing the whole feed.
    """
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.min


def get_findings_feed(max_research: int = 10, max_industry: int = 10) -> list[dict]:
    """
    Merges arXiv research papers and GNews industry news into a single feed,
    sorted by recency (newest first).
    """
    research = fetch_arxiv_papers(max_results=max_research)
    industry = fetch_industry_news(max_articles=max_industry)

    combined = research + industry
    combined.sort(key=lambda item: _parse_date_safe(item["published_at"]), reverse=True)

    return combined


if __name__ == "__main__":
    feed = get_findings_feed(max_research=5, max_industry=5)
    for item in feed:
        print(f"[{item['tag']}] {item['title']} — {item['source']} ({item['published_at']})")
