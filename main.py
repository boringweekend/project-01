from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import os

from app.rag_engine import rag_engine
from app.llm_service import llm_service
from app.ocr_utils import extract_text_from_pdf

app = FastAPI(title="Legal Chatbot")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount moved to end of file

class ChatRequest(BaseModel):
    message: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Save file temporarily
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Read file bytes for OCR/Text extraction
        with open(temp_path, "rb") as f:
            file_bytes = f.read()

        # Extract text
        print(f"Processing {file.filename}...")
        text = extract_text_from_pdf(file_bytes)
        
        # Ingest into RAG
        rag_engine.ingest_document(file.filename, text)
        
        # Cleanup
        os.remove(temp_path)
        
        return {"filename": file.filename, "status": "Ingested successfully", "extracted_chars": len(text)}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

@app.post("/chat")
async def chat(request: ChatRequest):
    user_query = request.message
    
    # 1. Retrieve context
    context_docs = rag_engine.search(user_query)
    context_str = "\n\n".join(context_docs)
    
    # 2. Construct Prompt
    system_prompt = f"""You are a helpful legal assistant. Use the following context to answer the user's question.
    
    Guidelines:
    - Format your answer using Markdown (bold, bullet points, headers) for readability.
    - Be concise and professional.
    - If the answer is not in the context, say you don't know.
    
    Context:
    {context_str}
    """
    
    # 3. Generate Response
    import time
    start_time = time.time()
    response = llm_service.generate_response(user_query, system_prompt=system_prompt)
    end_time = time.time()
    duration = end_time - start_time
    
    return {"response": response, "context": context_docs, "time_taken": duration}

# Mount static files for frontend (Must be last to avoid shadowing API routes)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
