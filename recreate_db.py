import psycopg2

DB_HOST = "localhost"
DB_NAME = "rag_db"
DB_USER = "rag_user"
DB_PASS = "rag_password"

conn = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASS
)

conn.autocommit = True
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS documents;")
cursor.execute("""
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content_type VARCHAR(50) NOT NULL,
    text_content TEXT,
    image_path TEXT,
    embedding VECTOR(3072),
    source_filename TEXT
);
""")


print("Database recreated with 3072 dimensions.")
cursor.close()
conn.close()
