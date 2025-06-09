# backend/app/services/llm_gemini.py

import os
import time
from typing import List, Dict

from dotenv import load_dotenv
from google import genai
from google.genai import types as GeminiTypes

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_API_KEY is None:
    raise RuntimeError("Environment variable GOOGLE_API_KEY not found")

client_gemini = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = (
    "You are an expert assistant on the Shakers platform. "
    "Answer in the same language as the user's question, using only the information provided in the snippets."
)

FEW_SHOT_EXAMPLES = [
    {
        "excerpts": [
            {
                "text": "In Shakers, payments are processed as follows: the client deposits funds...",
                "source": "payments.md#chunk_0",
            },
            {
                "text": "Credit cards and PayPal are accepted. Fees vary by country.",
                "source": "payments_methods.md#chunk_1",
            },
        ],
        "query": "How do payments work on Shakers?",
        "answer": (
            "On Shakers, payments are made via credit card or PayPal. "
            "Once the client approves the completed work, the held funds are released to the freelancer."
        ),
    },
]


def generate_answer_with_references_gemini(
    snippet_texts: List[str],
    query: str,
    model: str = "gemini-2.0-flash",
) -> Dict[str, object]:
    """
    Builds a prompt with:
      1) System instruction.
      2) Few-shot examples.
      3) Provided snippet_texts.
      4) The user's question.
    Calls Gemini and returns a dict with:
      - 'answer': generated text
      - 'gemini_time_seconds': elapsed API call time
    """

    # 1) Build the snippets section of the prompt
    prompt_fragments = ""
    for idx, text in enumerate(snippet_texts, start=1):
        clean_text = text.strip().replace("\n", " ")
        prompt_fragments += f"Snippet {idx}: {clean_text}\n"

    # 2) Build the few-shot examples section
    few_shot_text = ""
    for example in FEW_SHOT_EXAMPLES:
        few_shot_text += "Example:\n"
        for exc in example["excerpts"]:
            few_shot_text += f"Snippet: {exc['text']}\n"
        few_shot_text += f"Question: {example['query']}\n"
        few_shot_text += f"Answer: {example['answer']}\n\n"

    # 3) Construct the full prompt
    full_prompt = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"{few_shot_text}"
        f"Your snippets:\n{prompt_fragments}\n"
        f"Question: {query.strip()}\n\n"
        "Answer:"
    )

    # 4) Call the Gemini API
    start_time = time.time()
    try:
        response = client_gemini.models.generate_content(
            model=model,
            config=GeminiTypes.GenerateContentConfig(system_instruction=""),
            contents=full_prompt,
        )
    except Exception as e:
        raise RuntimeError(f"Error calling Gemini: {e}")
    elapsed = time.time() - start_time

    generated_text = response.text.strip()

    return {
        "answer": generated_text,
        "gemini_time_seconds": elapsed,
    }
