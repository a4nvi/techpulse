from fastapi import FastAPI
from routes.api import router
app = FastAPI(title="Techpulse API")
app.include_router(router)  # Include the API router for news endpoints

@app.get("/")
def health_check():
    return {"STATUS": "OK", "message": "Techpulse API is running!"}

# What it's for: It's a super common pattern in backend development — a simple endpoint whose only job is to answer "is this server up and running?" When you hit http://127.0.0.1:8000/, it just replies with a basic JSON confirming the server is alive, without doing any real work (no database calls, no external API calls).

# Why it matters in practice: When you deploy TechPulse later, hosting platforms (like Render, Railway, etc.) often ping a health-check endpoint automatically to confirm your app didn't crash.
# If something's broken, hitting / first tells you instantly whether the problem is "server won't start at all" vs. "server's fine, but this specific endpoint has a bug." It's your first line of debugging.
# It's a convention, not something specific to FastAPI — Node/Express, Django, etc. all use this same idea.

# In TechPulse's case specifically, it's not doing anything fancy — just confirming the FastAPI app booted correctly before we layer on the real endpoints (/api/news-test, and soon /api/trends, /api/market, /api/findings from your spec).
