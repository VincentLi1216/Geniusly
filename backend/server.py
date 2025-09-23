import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI


# docs: http://127.0.0.1:8000/docs


# -------- Environment & Client Setup --------
# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4.1-mini")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing. Please set it in your environment or .env file.")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# -------- FastAPI App --------
app = FastAPI(title="Topic & Script API", version="1.1.0")

# Enable CORS (for dev, adjust in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------- Pydantic Schemas --------
class SuggestTopicsRequest(BaseModel):
    user_interest: str = Field(..., description="The user's learning interest or area.")
    model: Optional[str] = Field(None, description="OpenAI model name (optional).")

class SuggestTopicsResponse(BaseModel):
    raw: str
    topics: List[str]

class BuildChatRequest(BaseModel):
    topic: str = Field(..., description="Chosen topic for the script.")
    model: Optional[str] = Field(None, description="OpenAI model name (optional).")

class ChatResponse(BaseModel):
    script: str

# -------- Helpers --------
def parse_topics_from_text(text: str) -> List[str]:
    """Parse model response into a clean list of topics."""
    lines = [ln.strip(" -•*\t") for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    parsed: List[str] = []
    for ln in lines:
        for prefix in ["1.", "2.", "3.", "4.", "5.", "1)", "2)", "3)", "4)", "5)"]:
            if ln.lower().startswith(prefix):
                ln = ln[len(prefix):].strip()
                break
        parsed.append(ln)
    parsed = [p for p in parsed if p]
    if len(parsed) > 5:
        parsed = parsed[:5]
    return parsed or lines[:5]

# -------- Routes --------
@app.post("/suggest-topics", response_model=SuggestTopicsResponse)
def suggest_topics(payload: SuggestTopicsRequest) -> SuggestTopicsResponse:
    """Generate topic suggestions based on user interest."""
    try:
        model_name = payload.model or DEFAULT_MODEL
        system_prompt = (
            "You are a creative tutor. Your job is to suggest 5 fun, specific, and "
            "engaging video topics that are good for a short educational skit."
        )
        user_prompt = (
            f"The user wants to learn about: {payload.user_interest}\n"
            "Please suggest 5 possible video topics."
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        resp = client.chat.completions.create(model=model_name, messages=messages)
        raw_text = resp.choices[0].message.content
        topics = parse_topics_from_text(raw_text)
        return SuggestTopicsResponse(raw=raw_text, topics=topics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topic suggestions: {e}")

@app.post("/line-generation", response_model=ChatResponse)
def chat(payload: BuildChatRequest) -> ChatResponse:
    """Generate a Family Guy style script for the given topic."""
    try:
        model_name = payload.model or DEFAULT_MODEL

        # Fixed system prompt (Family Guy style)
        system_prompt = """You are to roleplay as characters from Family Guy in a short script (about 1 minute long).

Characters:
- Stewie: sarcastic, highly intelligent baby, curious, asks sharp questions.
- Peter: goofy, clueless father, often makes silly analogies but sometimes stumbles into the right explanation.

Rules:
1. Dialogue should alternate between Stewie and Peter, starting with Stewie asking a question.
2. Keep it short and snappy, like a cartoon skit (10-12 lines total).
3. Humor is essential—Peter's answers should be funny, sometimes absurd, but loosely tied to the real explanation.
4. Stewie should occasionally roast Peter's stupidity but also clarify the correct idea.
5. The script must feel like a Family Guy cutaway gag: sarcastic, humorous, and fast-paced.
6. Output format:
   Stewie: …
   Peter: …

Do not include narration or stage directions—just pure dialogue.
"""

        user_prompt = f"Topic: {payload.topic}\nWrite the script."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        resp = client.chat.completions.create(model=model_name, messages=messages)
        script = resp.choices[0].message.content
        return ChatResponse(script=script)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate script: {e}")
