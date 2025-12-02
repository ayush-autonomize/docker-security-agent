from fastapi import FastAPI
from dotenv import load_dotenv
from .routes_repos import router as repos_router
from .routes_scans import router as scans_router

# Load environment variables (GITHUB_TOKEN, etc.)
load_dotenv()

app = FastAPI(title="Docker Security Agent API")

# Include Routers
app.include_router(repos_router)
app.include_router(scans_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
