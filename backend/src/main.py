from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Weak Signals API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str


@app.get("/")
def root():
    return {"status": "ok", "service": "Weak Signals API", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/api/search")
def create_search(request: SearchRequest):
    return {
        "search_id": "stub-001",
        "query": request.query,
        "status": "queued",
    }


@app.get("/api/search/{search_id}")
def get_search(search_id: str):
    return {
        "search_id": search_id,
        "status": "completed",
        "signals": [],
    }


@app.get("/api/stats")
def stats():
    return {
        "total_candidates": 0,
        "processed_sources": 0,
        "signals_above_75": 0,
    }