import os
import tempfile
import uvicorn
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from typing import Optional

# Import DiseaseEngine and AgroBotEngine packages
from app.inference import DiseaseEngine
from app.agrobot import AgroBotEngine

app = FastAPI(
    title="AgroIntelli AI Engine",
    description="Backend API for Offline Plant Pathology Inference & Bilingual Farming Advisory",
    version="1.0.0"
)

# Enable CORS for local testing if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize deep learning inference engine and AgroBot
engine = DiseaseEngine()
agrobot = AgroBotEngine()


class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "auto"  # "auto", "en", "bn"
    diagnosis_context: Optional[str] = None


@app.post("/predict")
async def predict_leaf(
    file: UploadFile = File(...),
    field_mode: bool = Query(True, description="Enable Field Mode confidence thresholding")
):
    # Determine file extension to prevent Pillow issues
    _, ext = os.path.splitext(file.filename or "")
    if not ext:
        ext = ".jpg"
        
    # Write incoming file to temporary location
    # Windows requires closing file descriptor before opening it elsewhere (like in PIL)
    fd, temp_path = tempfile.mkstemp(suffix=ext)
    try:
        with os.fdopen(fd, "wb") as tmp:
            content = await file.read()
            tmp.write(content)
            
        # Perform image validation, severity proxy, and neural inference
        result = engine.predict(temp_path, field_mode=field_mode)
        return result
        
    except Exception as e:
        return {"ok": False, "error": str(e)}
        
    finally:
        # Clean up temporary file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass


@app.post("/chat")
async def chat_with_bot(req: ChatRequest):
    """Bilingual conversational endpoint for agricultural advice."""
    try:
        lang_pref = req.language if req.language in ("en", "bn") else None
        res = agrobot.answer_query(
            query=req.message,
            lang_pref=lang_pref,
            diagnosis_context=req.diagnosis_context
        )
        return res
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "reply": "দুঃখিত, উত্তর দিতে সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।" if req.language == "bn" else "Sorry, an error occurred while processing your request. Please try again."
        }


@app.get("/chat/quick-topics")
async def quick_topics():
    """Retrieve quick prompt suggestion chips for English and Bangla."""
    return agrobot.get_quick_topics()


# Mount static files at root directory
# html=True automatically serves index.html at "/"
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  AgroIntelli AI & Bilingual AgroBot Server Running")
    print("  - Localhost: http://localhost:8000")
    print("  - Local Network: http://0.0.0.0:8000")
    print("=" * 55 + "\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
