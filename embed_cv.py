from pathlib import Path

from sentence_transformers import SentenceTransformer


def embed_cv(file_path: str) -> None:
    """
    Reads a text file (or PDF converted to text), chunks it,
    embeds it using sentence-transformers, and uploads to Supabase.
    """
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Simple chunking logic (for demonstration)
    content = Path(file_path).read_text()

    chunks = content.split('\n\n')  # Split by paragraphs

    for _i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        _embedding = model.encode(chunk).tolist()

        # supabase.table("cv_chunks").insert({
        #     "content": chunk,
        #     "embedding": _embedding,
        #     "metadata": {"chunk_id": i}
        # }).execute()


if __name__ == '__main__':
    # Ensure you have a cv.txt file or modify this to handle PDFs
    if Path('cv.txt').exists():
        embed_cv('cv.txt')
