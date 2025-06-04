# backend/app/services/llm_gemini.py

import os
import time
from typing import List, Dict

from dotenv import load_dotenv

# Import the Gemini client and types
from google import genai
from google.genai import types as GeminiTypes

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
if GEMINI_API_KEY is None:
    raise RuntimeError("Environment variable GOOGLE_API_KEY not found")

client_gemini = genai.Client(api_key=GEMINI_API_KEY)

# 1) Fixed system instruction text (answer in the same language as the query)
SYSTEM_INSTRUCTION = (
    "You are an expert assistant on the Shakers platform. "
    "Answer in the same language as the user's question, using only the information provided in the snippets. "
    "When you finish, include a section titled 'References' at the end, listing the exact source files (file.md and chunk) you used."
)

# 2) Two brief examples in English (few-shot)
FEW_SHOT_EXAMPLES = [
    {
        "excerpts": [
            {
                "source": "payments.md#chunk_0",
                "text": "In Shakers, payments are processed as follows: the client deposits funds, which are held in escrow until the delivery of the work.",
            },
            {
                "source": "payments_methods.md#chunk_1",
                "text": "Credit cards and PayPal are accepted. Fees vary by country.",
            },
        ],
        "query": "How do payments work on Shakers?",
        "answer": (
            "On Shakers, payments are made via credit card or PayPal. "
            "Once the client approves the completed work, the held funds are released to the freelancer."
            "\n\nReferences:\n"
            "- payments.md#chunk_0\n"
            "- payments_methods.md#chunk_1"
        ),
    },
    {
        "excerpts": [
            {
                "source": "freelancer.md#chunk_0",
                "text": "A freelancer is an independent professional offering services via Shakers.",
            },
            {
                "source": "freelancer.md#chunk_2",
                "text": "To become a freelancer, you must complete your profile with skills and experience.",
            },
        ],
        "query": "What is a freelancer on Shakers?",
        "answer": (
            "On Shakers, a freelancer is an independent professional offering services directly to clients. "
            "To register, you must create a detailed profile listing your skills and experience."
            "\n\nReferences:\n"
            "- freelancer.md#chunk_0\n"
            "- freelancer.md#chunk_2"
        ),
    },
]


def generate_answer_with_references_gemini(
    fragments: List[Dict[str, object]],
    query: str,
    model: str = "gemini-2.0-flash",
) -> Dict[str, object]:
    """
    Builds a structured prompt with:
      1) System instruction.
      2) Few-shot examples.
      3) Retrieved snippets.
      4) The user's question.
    Calls Gemini and returns:
      {
        "answer": generated text,
        "references": [list of sources],
        "gemini_time_seconds": time in seconds
      }
    """

    # 1. Sort fragments by score (distance) ascending (closest first)
    sorted_frags = sorted(fragments, key=lambda f: f["score"])

    # 2. Build the fragments section in the prompt
    prompt_fragments = ""
    for idx, frag in enumerate(sorted_frags, start=1):
        src = frag["source"]
        txt = frag["text"].strip().replace("\n", " ")
        prompt_fragments += f"Snippet {idx} (source: {src}):\n{txt}\n\n"

    # 3. Build the few-shot part with pre-formatted examples
    few_shot_text = ""
    for ex in FEW_SHOT_EXAMPLES:
        few_shot_text += "Example:\n"
        for f in ex["excerpts"]:
            few_shot_text += f"Snippet (source: {f['source']}):\n{f['text']}\n\n"
        few_shot_text += f"Question: \"{ex['query']}\"\n"
        few_shot_text += f"Answer: \"{ex['answer']}\"\n\n"

    # 4. Construct the final prompt by concatenating:
    #    - System instruction
    #    - Few-shot
    #    - Section “Your snippets”
    #    - The user's question
    full_prompt = (
        f"{SYSTEM_INSTRUCTION}\n\n"
        f"{few_shot_text}"
        f"Your snippets:\n"
        f"{prompt_fragments}"
        f'Question: "{query.strip()}"\n\n'
        f"Answer:"
    )

    # 5. Call Gemini using models.generate_content
    start_time = time.time()
    try:
        response = client_gemini.models.generate_content(
            model=model,
            config=GeminiTypes.GenerateContentConfig(system_instruction=""),
            contents=full_prompt,
        )
        elapsed = time.time() - start_time
    except Exception as e:
        raise RuntimeError(f"Error calling Gemini: {e}")

    # 6. Extract generated text from response.text
    generated_text = response.text.strip()

    # 7. Extract the list of references from the generated text
    #    We look for the line starting with “References:” and then take any following lines starting with “- ” or “* ”.
    references = []
    for line in generated_text.splitlines():
        if line.strip().lower().startswith("references"):
            continue  # skip the header line
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            ref = line.strip()[2:]
            references.append(ref)

    # 8. If no references were found in the text, use the sorted fragments list
    if not references:
        references = [frag["source"] for frag in sorted_frags]

    return {
        "answer": generated_text,
        "references": references,
        "gemini_time_seconds": elapsed,
    }
