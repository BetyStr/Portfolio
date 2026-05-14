import os
from pathlib import Path

from google import genai


def embed_cv(file_path: str) -> None:
    """
    Reads a text file, chunks it, embeds it using Gemini API,
    and prepares it for Supabase.
    """
    # 1. Init Client
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return

    client = genai.Client(api_key=api_key)

    # 2. Read Content
    content = Path(file_path).read_text()
    chunks = [c.strip() for c in content.split('\n\n') if c.strip()]

    # 3. Embed and Log
    for _i, chunk in enumerate(chunks):
        try:
            res = client.models.embed_content(
                model='text-embedding-004',
                contents=chunk,
            )
            _embedding = res.embeddings[0].values

            # Note: You would push to Supabase here.
            # Dimensions: 768 for text-embedding-004
            # supabase.table("cv_chunks").insert({
            #     "content": chunk,
            #     "embedding": _embedding,
            #     "metadata": {"chunk_id": i}
            # }).execute()
        except Exception:  # noqa: S110
            pass


if __name__ == '__main__':
    if Path('cv.txt').exists():
        embed_cv('cv.txt')
