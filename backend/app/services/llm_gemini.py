# backend/app/services/llm_gemini.py

import os
import time
from typing import List, Dict

from dotenv import load_dotenv

# Importamos el cliente y tipos desde google.genai
from google import genai
from google.genai import types as GeminiTypes

load_dotenv()
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")  # o "GEMINI_API_KEY" según tu .env
if GEMINI_API_KEY is None:
    raise RuntimeError("No se encontró la variable de entorno GOOGLE_API_KEY")

# Inicializamos el cliente de Gemini
client_gemini = genai.Client(api_key=GEMINI_API_KEY)

# Instrucción de sistema: rol/tarea del asistente
INSTRUCCION_SISTEMA = (
    "Eres un asistente experto en la plataforma Shakers. "
    "A partir de los fragmentos de la base de conocimiento que te proporcione, "
    "responde de forma clara y concisa a la pregunta del usuario. "
    "Al final de tu respuesta, incluye una sección titulada 'Referencias' "
    "con la lista de fuentes (archivo.md y chunk) que utilizaste."
)


def generate_answer_with_references_gemini(
    fragments: List[Dict[str, object]],
    query: str,
    model: str = "gemini-2.0-flash",
) -> Dict[str, object]:
    """
    Construye un payload a partir de los fragments (cada uno con 'text' y 'source'),
    invoca a Gemini usando models.generate_content(...) y devuelve:
      {
        "answer": texto_generado_por_Gemini,
        "references": [lista_de_sources_utilizados],
        "gemini_time_seconds": tiempo que tardó la llamada
      }
    """

    # 1. Ordenamos los fragments por 'score' descendente
    sorted_frags = sorted(fragments, key=lambda f: f["score"], reverse=True)

    # 2. Construimos la parte de fragments como texto
    prompt_fragments = ""
    for idx, frag in enumerate(sorted_frags, start=1):
        source = frag["source"]
        text = frag["text"].strip().replace("\n", " ")
        prompt_fragments += f"Fragmento {idx} (origen: {source}):\n{text}\n\n"

    # 3. Concatenamos la instrucción de sistema + fragments + pregunta en un solo string
    payload = (
        f"{prompt_fragments}"
        f'Pregunta del usuario: "{query.strip()}"\n\n'
        f"Por favor, responde basándote en los fragmentos anteriores."
    )

    # 4. Llamamos a Gemini usando models.generate_content(...)
    start_time = time.time()
    try:
        response = client_gemini.models.generate_content(
            model=model,
            config=GeminiTypes.GenerateContentConfig(
                system_instruction=INSTRUCCION_SISTEMA
            ),
            contents=payload,
        )
        elapsed = time.time() - start_time
    except Exception as e:
        raise RuntimeError(f"Error al llamar a Gemini: {e}")

    # 5. Extraemos el texto generado:
    #    En esta versión, el resultado está en response.text
    generated_text = response.text.strip()

    # 6. Recolectamos la lista de referencias (sources) de los fragments que usamos
    references = [frag["source"] for frag in sorted_frags]

    return {
        "answer": generated_text,
        "references": references,
        "gemini_time_seconds": elapsed,
    }
