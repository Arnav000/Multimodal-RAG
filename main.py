import os
import shutil
import psycopg2
from fastapi import FastAPI, HTTPException, UploadFile, File
from ingest import process_and_ingest
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Multimodal RAG API")

# Setup CORS so the frontend can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini Client
client = genai.Client()

DB_HOST = "localhost"
DB_NAME = "rag_db"
DB_USER = "rag_user"
DB_PASS = "rag_password"

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

class ChatRequest(BaseModel):
    query: str

class SourceItem(BaseModel):
    content_type: str
    content: str
    filename: str
    similarity: float

class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]

def embed_query(query_text: str):
    response = client.models.embed_content(
        model='gemini-embedding-001',
        contents=query_text,
    )
    return response.embeddings[0].values

@app.post("/ask", response_model=ChatResponse)
def ask_question(req: ChatRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        # Step 1: Embed the user query
        query_vector = embed_query(req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to embed query: {e}")

    # Step 2: Search PostgreSQL using pgvector (Top 5 matches)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # We use <=> for cosine distance. 
        # Similarity = 1 - cosine_distance. 
        # But we order by distance ascending.
        # Note: We filter out rows where embedding is NULL (our image rows currently if we rely on true multimodal via vertex).
        # We'll just search text rows for now to get context, or any row with a vector.
        
        cursor.execute(
            """
            SELECT content_type, text_content, image_path, source_filename, 
                   1 - (embedding <=> %s::vector) AS similarity
            FROM documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT 5;
            """,
            (query_vector, query_vector)
        )
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database search failed: {e}")

    # Step 3: Format Context and Images
    context_texts = []
    sources = []
    
    for i, row in enumerate(results, 1):
        c_type, text_content, img_path, filename, sim = row
        
        if c_type == "text":
            context_texts.append(f"Source {i} ({filename}):\n{text_content}\n")
            sources.append(SourceItem(content_type="text", content=text_content, filename=filename, similarity=float(sim)))
        else:
            # If we had image vectors, we'd add the image file path to the prompt context for Gemini 1.5/2.5
            pass

    joined_context = "\n---\n".join(context_texts)

    # Step 4: Generate Answer with Gemini
    prompt = f"""
You are a helpful assistant answering a user's question based strictly on the provided context retrieved from a database.
Do not make up facts. If the answer is not in the context, say "I don't know based on the provided documents."

CONTEXT:
{joined_context}

USER QUESTION:
{req.query}
"""
    
    try:
        # We use gemini-1.5-flash or gemini-2.5-flash 
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        answer = response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation failed: {e}")

    return ChatResponse(answer=answer, sources=sources)

UPLOAD_DIR = "pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Run the ingestion process synchronously so the UI waits
        process_and_ingest(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
        
    return {"message": "File successfully uploaded and ingested"}
