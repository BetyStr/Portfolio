import os
from typing import Annotated, Any

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google import genai
from sentence_transformers import SentenceTransformer, util
from supabase import Client, create_client

app = FastAPI()

# Constants
THREAT_LOW = 10
THREAT_CRITICAL = 85
SIMILARITY_HIGH = 0.7
SIMILARITY_LOW = 0.3
GEMINI_MODEL = 'gemini-1.5-flash'
TARGET_WORD = 'ocean'

# Lazy-loaded globals
_model: SentenceTransformer | None = None
_target_emb: Any = None

# Init Gemini (Requires GOOGLE_API_KEY in .env)
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
ai_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None

# Mount static files (CSS, JS, Arcade games)
app.mount('/static', StaticFiles(directory='static'), name='static')

# Setup Jinja2 templates
templates = Jinja2Templates(directory='templates')

# Init Supabase
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


def get_model() -> SentenceTransformer:
    """Lazy-load the SentenceTransformer model."""
    global _model  # noqa: PLW0603
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def get_target_emb() -> Any:
    """Lazy-load the target word embedding."""
    global _target_emb  # noqa: PLW0603
    if _target_emb is None:
        m = get_model()
        _target_emb = m.encode(TARGET_WORD)
    return _target_emb


@app.get('/', response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, 'index.html')


@app.get('/jailbreak', response_class=HTMLResponse)
async def jailbreak_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, 'jailbreak.html')


@app.post('/api/jailbreak', response_class=HTMLResponse)
async def handle_jailbreak(_request: Request, prompt: Annotated[str, Form()]) -> str:
    # 1. Guardrail Check & Attack Detection
    attack_detected = 'None'
    threat_level = THREAT_LOW
    color = 'green'
    status = 'Low'

    forbidden_words = ['ignore', 'system prompt', 'developer mode', 'jailbreak']
    if any(word in prompt.lower() for word in forbidden_words):
        attack_detected = 'Prompt Injection'
        threat_level = THREAT_CRITICAL
        color = 'red'
        status = 'CRITICAL'
        ai_response = '[GUARDRAIL ACTIVE] Access Denied. Your attempt has been logged.'
        bubble_class = 'bg-red-900/50 border-red-500 text-red-200'
    else:
        # 2. LLM Call
        if ai_client:
            try:
                response = ai_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=f'You are a secure bank vault. A user says: {prompt}. Respond stay in character.',
                )
                ai_response = response.text
            except Exception as e:
                ai_response = f'I am currently offline. Error: {e!s}'
        else:
            ai_response = 'I am a bank vault. I will not tell you.'
        bubble_class = 'bg-gray-700 text-gray-100 border-gray-600'

    # 3. Return the chat bubble AND OOB updates for the console
    return f"""
    <div class='flex flex-col gap-3 mb-4 animate-in fade-in slide-in-from-bottom-2 duration-300'>
        <div class='self-end bg-blue-600 text-white p-3 rounded-2xl rounded-tr-none max-w-[80%] shadow-lg'>
            <p class='text-xs opacity-70 mb-1'>You</p>
            {prompt}
        </div>
        <div class='self-start {bubble_class} p-3 rounded-2xl rounded-tl-none max-w-[80%] border shadow-lg'>
            <p class='text-xs text-blue-400 mb-1'>AI Vault</p>
            {ai_response}
        </div>
    </div>

    <!-- OOB Updates for Security Console -->
    <div id="security-console" hx-swap-oob="afterbegin">
        <div class="p-3 bg-white/5 rounded border border-white/5 text-{color}-400 mb-2 animate-pulse">
            > [{attack_detected}] detected in: "{prompt[:20]}..."
        </div>
    </div>
    <div id="threat-status" hx-swap-oob="innerHTML" class="text-{color}-500">{status}</div>
    <div id="threat-bar" hx-swap-oob="style:width" class="bg-{color}-500">{threat_level}%</div>
    """


@app.post('/api/ask-cv', response_class=HTMLResponse)
async def ask_cv(_request: Request, question: Annotated[str, Form()]) -> str:
    if not supabase or not ai_client:
        return "<div class='p-4 bg-red-500/20 text-red-400 rounded-xl'>Supabase or Gemini not configured.</div>"

    # 1. Embed the question (Lazy Loading)
    m = get_model()
    query_vector = m.encode(question).tolist()

    # 2. Query Supabase for context
    try:
        response = supabase.rpc(
            'match_cv_chunks', {'query_embedding': query_vector, 'match_threshold': 0.5, 'match_count': 3}
        ).execute()

        context = ' '.join([item['content'] for item in response.data])
    except Exception as e:
        context = f'Error fetching context: {e!s}'

    # 3. Prompt the LLM
    llm_prompt = (
        f"Using this context: {context}. Answer the user's question about Alzbeta's CV: {question}. "
        'Keep it professional and concise.'
    )
    ai_answer = ai_client.models.generate_content(model=GEMINI_MODEL, contents=llm_prompt).text

    return f"""
    <div class='p-6 glass rounded-2xl border-l-4 border-blue-500 animate-in fade-in'>
        <p class='text-xs text-blue-400 mb-2 font-bold uppercase'>AI Assistant</p>
        <div class='prose prose-invert text-gray-200'>{ai_answer}</div>
    </div>
    """


@app.post('/api/semantic', response_class=HTMLResponse)
async def check_semantic(_request: Request, guess: Annotated[str, Form()]) -> str:
    m = get_model()
    target_emb = get_target_emb()
    guess_emb = m.encode(guess)
    score = util.cos_sim(target_emb, guess_emb).item()

    # Format score and return HTML progress bar or text
    color = 'bg-blue-500'
    if score > SIMILARITY_HIGH:
        color = 'bg-green-500'
    elif score < SIMILARITY_LOW:
        color = 'bg-red-500'

    percentage = int(max(0, min(1, score)) * 100)

    return f"""
    <div class="mt-4 p-4 bg-gray-800/50 rounded-xl border border-white/5 animate-in fade-in slide-in-from-bottom-2">
        <div class="flex justify-between mb-2">
            <span class="text-sm font-medium text-gray-400">
                Similarity for <span class="text-white font-bold">"{guess}"</span>
            </span>
            <span class="text-sm font-bold text-blue-400">{(score * 100):.1f}%</span>
        </div>
        <div class="w-full bg-gray-900 rounded-full h-2 overflow-hidden">
            <div class="{color} h-full rounded-full transition-all duration-1000 ease-out"
                 style="width: {percentage}%"></div>
        </div>
    </div>
    """


@app.get('/arcade', response_class=HTMLResponse)
async def arcade_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, 'arcade.html')


@app.post('/api/scores')
async def save_score(
    _game: Annotated[str, Form()], _score: Annotated[int, Form()], _player: Annotated[str, Form()]
) -> str:
    # supabase.table("arcade_scores").insert({"game": game, "score": score, "player": player}).execute()
    return 'Score saved!'
