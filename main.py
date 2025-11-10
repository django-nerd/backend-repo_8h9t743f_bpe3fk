import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents, db
from schemas import Entry

app = FastAPI(title="Personal Creative Hub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Personal Creative Hub Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Models for requests
class CreateEntryRequest(BaseModel):
    category: str
    title: str
    content: str
    tags: Optional[List[str]] = None
    mood: Optional[str] = None

@app.post("/api/entries")
def create_entry(payload: CreateEntryRequest):
    try:
        entry = Entry(
            category=payload.category,
            title=payload.title,
            content=payload.content,
            tags=payload.tags,
            mood=payload.mood,
        )
        entry_id = create_document("entry", entry)
        return {"id": entry_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/entries")
def list_entries(category: Optional[str] = None, limit: int = 50):
    try:
        filter_dict = {"category": category} if category else {}
        docs = get_documents("entry", filter_dict, limit)
        # Convert ObjectId and datetime fields to strings
        def transform(doc):
            doc["_id"] = str(doc.get("_id"))
            for key in ["created_at", "updated_at"]:
                if key in doc and doc[key] is not None:
                    doc[key] = str(doc[key])
            return doc
        return [transform(d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
