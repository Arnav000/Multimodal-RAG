# Multimodal RAG Project

This repository contains a full-stack Multimodal Retrieval-Augmented Generation (RAG) backend powered by **FastAPI**, **PostgreSQL/pgvector**, and **Google Gemini** integration.

## Features

- **Document Ingestion:** Processes PDF files extracting text (and theoretically images) chunks.
- **Vector Search:** Converts text into embeddings (via `gemini-embedding-001`) and performs fast similarity searches using `pgvector`.
- **Chat API:** Uses context mapped from vector searches to answer user queries with `gemini-2.5-flash`.
- **Frontend UI:** Interactive Chat and Document uploading natively in `index.html`.

## Working

https://github.com/user-attachments/assets/b9abde3c-690a-4888-b6ee-36525ac3b630

## Prerequisites

- Python 3.9+
- Docker and Docker Compose (to run the PostgreSQL + pgvector instance)
- A `.env` file containing your valid **Google Gemini API Key**:
  ```env
  GEMINI_API_KEY=your_api_key_here
  ```

## Getting Started

1. **Install Python Dependencies:**
   Make sure you use a virtual environment (`venv`).
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Database:**
   Use the included docker configuration to effortlessly boot a pgvector compatible PostgreSQL wrapper.
   ```bash
   docker-compose up -d
   ```

3. **Start the FastAPI Backend:**
   Run the backend locally using `uvicorn`.
   ```bash
   uvicorn main:app --reload
   ```

4. **Access the Frontend:**
   Open `index.html` in your web browser, or serve it securely via your preferred web server tool (e.g. VS Code's Live Server extension).

## Recommended Folder Structure

When the repository grows, consider separating the structure logically to keep it organized:
- `/src` - Core backend logic like `main.py`, `ingest.py`, etc.
- `/frontend` - Contains UI files such as `index.html` and static assets.
- `/tests` - Scratchpad validation scripts such as `test_dim.py`.

*Note: User-supplied `pdfs` and vector-mapped `images` are excluded by default via `.gitignore`.*
