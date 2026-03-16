-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the documents table
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(50) NOT NULL, -- 'text' or 'image'
    text_content TEXT,                 -- The chunked text (if type is text)
    image_path TEXT,                   -- The local path to the extracted image (if type is image)
    embedding VECTOR(3072),             -- The vector representation from text-embedding-004 (or multimodalembedding)
    source_filename TEXT               -- The name of the PDF this came from
);

-- Optional: Create an HNSW index to speed up vector searches (useful for larger datasets)
