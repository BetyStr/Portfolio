# 🚀 AI Portfolio: A Premium Experience

A state-of-the-art developer portfolio showcasing the intersection of **Generative AI**, **Semantic Search**, and **Modern Web Architecture**. This project isn't just a static resume; it's a living demonstration of RAG (Retrieval-Augmented Generation), LLM guardrails, and real-time interactive experiences.

![AI Portfolio Preview](https://via.placeholder.com/1200x600?text=Premium+AI+Portfolio+Interface)

## ✨ Key Features

### 🧠 The Digital Brain (RAG)
Interactive Q&A powered by **Google Gemini** and **Supabase Vector Storage**. The system uses `sentence-transformers` to embed my CV into a vector space, allowing for context-aware answers about my professional experience.

### 🛡️ Jailbreak Challenge & Security Console
A gamified demonstration of LLM safety.
- **The Challenge**: Try to trick the "AI Vault" into revealing secrets.
- **Security Console**: A real-time monitoring dashboard using **HTMX Out-of-Band (OOB) swaps** to visualize detected prompt injections and threat levels.

### 🔍 Semantic "Hot or Cold"
A demonstration of vector embeddings. Guess secret words based on their *meaning* rather than their spelling. High similarity scores are visualized with smooth, dynamic progress bars.

### 🕹️ AI Arcade
Classic games like **Snake AI** and **Tetris** with a modern twist.
- **Integrated Leaderboards**: Scores are automatically synced to Supabase.
- **Server-side High Scores**: Real-time competition tracking.

---

## 🛠️ Tech Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.14+)
- **Frontend**: [HTMX](https://htmx.org/) (High-power interactivity without JS complexity)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) with Custom Glassmorphism
- **Database**: [Supabase](https://supabase.com/) (PostgreSQL + Vector)
- **AI Models**: 
  - **LLM**: Google Gemini 1.5 Flash
  - **Embeddings**: `all-MiniLM-L6-v2` (Sentence-Transformers)
- **Package Manager**: [uv](https://github.com/astral-sh/uv)

---

## 🚀 Getting Started

### 1. Clone & Install
```bash
# Clone the repository
git clone <your-repo-url>
cd web

# Install dependencies using uv
uv sync
```

### 2. Environment Configuration
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Initialize the Vector Database
Populate the "Brain" with your CV:
1. Edit `cv.txt` with your details.
2. Run the embedding script:
```bash
uv run python embed_cv.py
```

### 4. Launch the Experience
```bash
uv run uvicorn main:app --reload
```
Visit `http://127.0.0.1:8000` to see your portfolio in action!

---

## 📜 Supabase SQL Setup
To enable the RAG feature, run the following SQL in your Supabase Editor:

```sql
-- Create a table for CV chunks
create table cv_chunks (
  id bigserial primary key,
  content text,
  embedding vector(768), -- Gemini text-embedding-004 dimensions
  metadata jsonb
);

-- Create the similarity search function
create or replace function match_cv_chunks (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table (
  id bigint,
  content text,
  similarity float
)
language plpgsql
as $$
begin
  return query
  select
    cv_chunks.id,
    cv_chunks.content,
    1 - (cv_chunks.embedding <=> query_embedding) as similarity
  from cv_chunks
  where 1 - (cv_chunks.embedding <=> query_embedding) > match_threshold
  order by similarity desc
  limit match_count;
end;
$$;
```

---

## 🛡️ License
MIT © 2024 Alzbeta Strompova
