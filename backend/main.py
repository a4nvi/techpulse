from fastapi import FastAPI
app = FastAPI(title="Techpulse API")

@app.get("/")
def health_check():
    return {"STATUS": "OK", "message": "Techpulse API is running!"}

