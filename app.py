from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os

from stego_engine import SemanticStegoEngine, generate_cover_paragraph

app = FastAPI(
    title="Semantic Steganography API",
    description="Full-stack API for embedding secret messages semantically into text using synonym substitution and AES encryption.",
    version="2.0.0"
)

# -----------------------------
# PYDANTIC SCHEMAS
# -----------------------------
class EncodeRequest(BaseModel):
    secret_text: str
    cover_text: Optional[str] = None
    password: Optional[str] = None
    auto_expand: Optional[bool] = True

class DecodeRequest(BaseModel):
    stego_text: str
    key_data: Dict[str, Any]
    password: Optional[str] = None

class GenerateCoverRequest(BaseModel):
    paragraphs_count: Optional[int] = 3

# -----------------------------
# API ENDPOINTS
# -----------------------------
@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Semantic Steganography API"}

@app.post("/api/encode")
def encode_message(req: EncodeRequest):
    try:
        cover = req.cover_text
        if not cover or not cover.strip():
            cover = generate_cover_paragraph(6)

        result = SemanticStegoEngine.encode(
            cover_text=cover.strip(),
            secret_text=req.secret_text,
            password=req.password if req.password and req.password.strip() else None,
            auto_expand=req.auto_expand
        )
        return {
            "success": True,
            "stego_text": result["stego_text"],
            "expanded_cover": result["expanded_cover"],
            "key_data": result["key_data"],
            "metrics": result["metrics"],
            "modifications": result["modifications"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/decode")
def decode_message(req: DecodeRequest):
    try:
        decoded_text = SemanticStegoEngine.decode(
            stego_text=req.stego_text,
            key_data=req.key_data,
            password=req.password if req.password and req.password.strip() else None
        )
        return {
            "success": True,
            "secret_text": decoded_text
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/generate-cover")
def generate_cover(req: GenerateCoverRequest):
    count = req.paragraphs_count or 3
    paras = [generate_cover_paragraph(5) for _ in range(count)]
    return {
        "success": True,
        "cover_text": "\n\n".join(paras)
    }

# -----------------------------
# STATIC FILES SERVING
# -----------------------------
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_frontend():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Semantic Steganography API running. Access /static/index.html or API endpoints."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
