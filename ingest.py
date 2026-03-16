import os
import fitz  # PyMuPDF
import psycopg2
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini Client
# It will automatically pick up GEMINI_API_KEY from the environment
if "GEMINI_API_KEY" not in os.environ or os.environ["GEMINI_API_KEY"] == "your_gemini_api_key_here":
    print("WARNING: GEMINI_API_KEY is not set properly in .env")

client = genai.Client()

# DB Connection settings
DB_HOST = "localhost"
DB_NAME = "rag_db"
DB_USER = "rag_user"
DB_PASS = "rag_password"

def create_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

def extract_pdf_content(pdf_path, image_output_dir="images"):
    """Extracts text and images from a PDF."""
    if not os.path.exists(image_output_dir):
        os.makedirs(image_output_dir)

    extracted_data = []
    filename = os.path.basename(pdf_path)
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Failed to open {pdf_path}: {e}")
        return extracted_data

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Extract Text
        text = page.get_text()
        if text.strip():
            chunks = chunk_text(text)
            for chunk in chunks:
                extracted_data.append({
                    "type": "text",
                    "content": chunk,
                    "filename": filename
                })

        # Extract Images
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list, start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            image_path = os.path.join(image_output_dir, f"{filename}_page{page_num+1}_img{img_index}.{image_ext}")
            
            with open(image_path, "wb") as f:
                f.write(image_bytes)
                
            extracted_data.append({
                "type": "image",
                "content": image_path,
                "filename": filename
            })

    return extracted_data

def embed_text(text):
    response = client.models.embed_content(
        model='gemini-embedding-001',
        contents=text,
    )
    return response.embeddings[0].values

def process_and_ingest(pdf_path):
    print(f"Processing {pdf_path}...")
    data_items = extract_pdf_content(pdf_path)
    
    conn = create_connection()
    cursor = conn.cursor()
    
    for item in data_items:
        try:
            if item["type"] == "text":
                embedding = embed_text(item["content"])
                cursor.execute(
                    """
                    INSERT INTO documents (content_type, text_content, embedding, source_filename)
                    VALUES (%s, %s, %s, %s)
                    """,
                    ("text", item["content"], embedding, item["filename"])
                )
                print(f"Inserted text chunk from {item['filename']}")
                
            elif item["type"] == "image":
                print(f"Found image: {item['content']}. NOTE: AI Studio currently primarily supports text-embedding models.")
                print("For a true multimodal vector database setup, you would use Vertex AI multimodalembedding@001 here.")
                print("If you have access to a multimodal embedding model via GenAI SDK, you'd embed the image bytes here.")
                # We will leave the embedding NULL or embed an empty array for now, unless we switch back to captioning.
                # Since user requested true multimodal but it requires Vertex AI mostly, we'll insert the row without embedding for now, 
                # or we can use gemini-1.5-flash to caption it as a fallback if true multimodal is not available on their free tier.
                
                # We will fall back to captioning for embedding purposes because true multimodal embeddings are gated behind Vertex AI GCS.
                # But to respect the user's Option B choice, let me just add a placeholder and explain.
                
                cursor.execute(
                    """
                    INSERT INTO documents (content_type, image_path, source_filename)
                    VALUES (%s, %s, %s)
                    """,
                    ("image", item["content"], item["filename"])
                )
                print(f"Inserted image reference from {item['filename']}")
                
        except Exception as e:
            print(f"Error inserting item: {e}")
            conn.rollback()
            continue
            
        conn.commit()

    cursor.close()
    conn.close()
    print("Ingestion complete.")

if __name__ == "__main__":
    if not os.path.exists("pdfs"):
        os.makedirs("pdfs")
        print("Created 'pdfs' directory. Please place a PDF in there and provide its path.")
    else:
        pdf_files = [f for f in os.listdir("pdfs") if f.endswith(".pdf")]
        if not pdf_files:
            print("No PDFs found in the 'pdfs' directory.")
        else:
            for pdf_file in pdf_files:
                process_and_ingest(os.path.join("pdfs", pdf_file))
