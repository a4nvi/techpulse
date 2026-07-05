import os
import requests  #library to make HTTP requests to external APIs.
from dotenv import load_dotenv  #library to load environment variables from a .env file.

load_dotenv()  #load environment variables from the .env file.

#without above two statements python cannot read the api key in .env file

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
GNEWS_BASE_URL = "https://gnews.io/api/v4/search"     #simply storing the API endpoint.

def fetch_tech_news(query: str="technology", max_articles: int=10) ->list[dict]:
    """
    Fetch tech news articles from GNews.
    Returns a list of simplified article dicts: title, description, url, published_at, source.
    """
    #help(fetch_tech_news) they will see above explanation
    if not GNEWS_API_KEY:                     #if api key not found
        raise ValueError("GNEWS_API_KEY is not set. Please check your .env file.")

    params = {
        "q": query,
        "lang": "en",
        "max": max_articles,
        "apikey": GNEWS_API_KEY,
    }

    #API request becomes:-
    #https://gnews.io/api/v4/search?
    #q=AI
    #&lang=en
    #&max=5
    #&apikey=abc123

    response = requests.get(GNEWS_BASE_URL, params=params)  #make a GET request to the GNews API with the specified parameters.
    #Please give me
    #AI news
    #English
    #5 articles
    #Here's my API key
    #everything stored in response variable

    response.raise_for_status()  # throws an error if GNews returns 4xx/5xx

    data = response.json()  #parse the JSON response from the API into a Python dictionary.
    articles = data.get("articles", [])

    return [
        {
            "title": a["title"],
            "description": a["description"],
            "url": a["url"],
            "published_at": a["publishedAt"],
            "source": a["source"]["name"],
        }
        for a in articles
    ]

    if __name__ == "__main__":
      articles = fetch_tech_news()
      for a in articles:
        print(a["title"], "-", a["source"])
