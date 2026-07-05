from fastapi import APIRouter
from services.news_fetcher import fetch_tech_news

router = APIRouter()

@router.get("/api/news-test")
def get_news_test():
    """Temporary test endpoint — confirms GNews integration works end-to-end."""
    articles = fetch_tech_news(max_articles=5)
    return {"count": len(articles), "articles": articles}
