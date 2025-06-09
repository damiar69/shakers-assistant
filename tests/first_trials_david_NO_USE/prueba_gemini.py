# tests/test_rag_pipeline_gemini.py

import os
import sys

# 1) Ajustamos ruta para importar el paquete "backend"
PROJECT_ROOT = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.services.retriever_openai import retrieve_fragments_openai
from backend.app.services.llm_gemini import generate_answer_with_references_gemini

# Definimos un umbral de distancia para clasificar consultas "out of scope".
# Con valores de prueba, típicamente < 1.0 indica cercano; > 1.0 indica lejano.
UMBRAL_DISTANCIA = 1.0


def main():
    # 1) Obtenemos la consulta (por argumento o input)
    if len(sys.argv) >= 2:
        query_text = " ".join(sys.argv[1:])
    else:
        query_text = input("Introduce la consulta que quieras probar: ").strip()
        if not query_text:
            print("No se ingresó ninguna consulta. Saliendo.")
            return

    print(f"\n=== PRUEBA RAG PIPELINE CON GEMINI ===\nQuery: {query_text}\n")

    # 2) Recuperar fragments (k = 3)
    k = 3
    frags = retrieve_fragments_openai(query_text, k=k)
    if not frags:
        print("No se recuperaron fragments. Verifica que la KB esté indexada.")
        return

    # 3) Determinar la distancia mínima entre la query y los fragments
    distancias = [score for (_, score, _) in frags]
    min_dist = min(distancias)

    # 4) Si min_dist > UMBRAL_DISTANCIA, la consulta está fuera de alcance
    if min_dist > UMBRAL_DISTANCIA:
        print(
            f"No hay información relevante (distancia mínima {min_dist:.3f} > umbral {UMBRAL_DISTANCIA})."
        )
        print("Lo siento, no tengo información sobre eso.")
        return

    # 5) Imprimir todos los fragments recuperados
    print(
        f"Se han recuperado {len(frags)} fragments (k={k}), min_dist={min_dist:.3f}:\n"
    )
    for idx, frag in enumerate(frags, start=1):
        texto, puntaje, origen = frag
        print(f"--- Fragmento {idx} ---")
        print(f"(dist = {puntaje:.3f})  from  {origen}\n")
        print(f"{texto}\n")
        print("-" * 60 + "\n")

    # 6) Convertir cada tupla a dict para llamar a Gemini
    frags_dict = [
        {"text": texto, "score": puntaje, "source": origen}
        for (texto, puntaje, origen) in frags
    ]

    # 7) Generar respuesta con Gemini
    rag_response = generate_answer_with_references_gemini(frags_dict, query_text)

    # 8) Mostrar la respuesta final
    print("\n--- Respuesta generada por Gemini ---")
    print(rag_response["answer"])
    print("\n--- Referencias ---")
    # Deduplicamos referencias por si Gemini las repite
    refs_dedup = list(dict.fromkeys(rag_response["references"]))
    for ref in refs_dedup:
        print(f" * {ref}")
    print(f"\n(Tiempo Gemini: {rag_response['gemini_time_seconds']:.2f} segundos)\n")


if __name__ == "__main__":
    main()
