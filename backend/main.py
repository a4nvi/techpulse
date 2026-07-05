from fastapi import FastAPI
from routes.api import router
app = FastAPI(title="Techpulse API")
app.include_router(router)  # Include the API router for news endpoints

@app.get("/")
def health_check():
    return {"STATUS": "OK", "message": "Techpulse API is running!"}

