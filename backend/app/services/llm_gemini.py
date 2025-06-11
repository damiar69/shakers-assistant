import os
import time
import logging
from typing import List, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types as GeminiTypes

# ─────────────────────────────────────────────────────────────────────────────
# Configure logging
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("llm_gemini")

# ─────────────────────────────────────────────────────────────────────────────
# Load Gemini API key
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_API_KEY is None:
    logger.error("Environment variable GOOGLE_API_KEY not found")
    raise RuntimeError("Environment variable GOOGLE_API_KEY not found")
client_gemini = genai.Client(api_key=GEMINI_API_KEY)
logger.info("Gemini client initialized")

# ─────────────────────────────────────────────────────────────────────────────
# System instruction
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_INSTRUCTION = (
    "You are an expert assistant on the Shakers platform. Answer in the lenguage of the user question.\n"
    "You will receive:\n"
    "  1) Several snippets labeled 'Snippet 1', 'Snippet 2', etc.,\n"
    "     each containing a portion of the knowledge base.\n"
    "  2) A user question to answer using only those snippets.\n"
    "Your task is:\n"
    "  • ANswer the question of the user  in plain text (no JSON, no Markdown, no quotes).\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# Few-shot examples
# ─────────────────────────────────────────────────────────────────────────────
FEW_SHOT_EXAMPLES = [
    {
        "excerpts": [
            {
                "text": "In Shakers, payments are processed as follows: the client deposits funds...",
                "source": "payments.md",
            },
            {
                "text": "Credit cards and PayPal are accepted. Fees vary by country.",
                "source": "payments_methods.md",
            },
        ],
        "query": "How do payments work on Shakers?",
        "answer": (
            "On Shakers, clients pay via credit card or PayPal. "
            "Funds are held in escrow until the work is approved, then released to the freelancer."
        ),
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Generate answer with references
# ─────────────────────────────────────────────────────────────────────────────
def generate_answer_with_references_gemini(
    snippet_texts: List[str],
    query: str,
    model: str = "gemini-2.0-flash",
) -> Dict[str, object]:
    """
    1) Build a prompt including:
       - SYSTEM_INSTRUCTION
       - Few-shot examples
       - Provided snippet_texts
       - The user's question
    2) Call Gemini to get a plain-text response.
    3) Return a dict with:
       - 'answer': the plain-text response
       - 'gemini_time_seconds': elapsed API call time
       - 'prompt': the full prompt (for debugging/logs)
    """

    # 1) Build snippet section
    prompt_fragments = ""
    for idx, text in enumerate(snippet_texts, start=1):
        clean = text.strip().replace("\n", " ")
        prompt_fragments += f"Snippet {idx}: {clean}\n"

    # 2) Build few-shot examples
    few_shot = ""
    for ex in FEW_SHOT_EXAMPLES:
        few_shot += "Example:\n"
        for exc in ex["excerpts"]:
            few_shot += f"Snippet: {exc['text']}\n"
        few_shot += f"Question: {ex['query']}\n"
        few_shot += f"Answer: {ex['answer']}\n\n"

    # 3) Construct full prompt
    full_prompt = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"{few_shot}"
        f"Your snippets:\n{prompt_fragments}\n"
        f"Question: {query.strip()}\n\n"
        "Answer:"
    )

    logger.debug("=== Prompt to Gemini ===")
    logger.debug(full_prompt)
    logger.debug("=== End prompt ===")

    # 4) Call Gemini
    start = time.time()
    try:
        response = client_gemini.models.generate_content(
            model=model,
            config=GeminiTypes.GenerateContentConfig(system_instruction=""),
            contents=full_prompt,
        )
    except Exception as e:
        logger.error(f"Gemini call error: {e}")
        raise
    elapsed = time.time() - start

    # 5) Extract plain-text answer
    answer = response.text.strip()
    logger.debug(f"Raw Gemini answer: {answer!r}")
    logger.info(f"Generated answer length={len(answer)} time={elapsed:.2f}s")

    return {
        "answer": answer,
        "gemini_time_seconds": elapsed,
        "prompt": full_prompt,
    }
