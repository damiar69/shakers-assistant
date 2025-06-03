# tests/test_rag_pipeline_gemini.py

import os
import sys

# 1) Ajustamos ruta para importar el paquete "backend"
PROJECT_ROOT = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.services.retriever_openai import retrieve_fragments_openai
from backend.app.services.llm_gemini import generate_answer_with_references_gemini


def main():
    # Si se pasa argumento por línea de comandos, lo usamos como query.
    # Si no, lo pedimos por input().
    if len(sys.argv) >= 2:
        query_text = " ".join(sys.argv[1:])
    else:
        query_text = input("Introduce la consulta que quieras probar: ").strip()
        if not query_text:
            print("No se ingresó ninguna consulta. Saliendo.")
            return

    print(f"\n=== PRUEBA RAG PIPELINE CON GEMINI ===\nQuery: {query_text}\n")

    # 1. Recuperar fragments (aquí recuperamos K = 3)
    k = 3
    frags = retrieve_fragments_openai(query_text, k=k)
    if not frags:
        print("No se recuperaron fragments. Verifica que la KB esté indexada.")
        return

    # 2. Imprimimos cuántos fragments hemos obtenido y su contenido completo
    print(f"Se han recuperado {len(frags)} fragments (k={k}):\n")
    for idx, frag in enumerate(frags, start=1):
        texto, puntaje, origen = frag
        print(f"--- Fragmento {idx} ---")
        print(f"(score = {puntaje:.3f})  from  {origen}\n")
        print(f"{texto}\n")
        print("-" * 60 + "\n")

    # 3. Convertimos cada tupla a dict para llamarlo a Gemini
    frags_dict = [
        {"text": texto, "score": puntaje, "source": origen}
        for (texto, puntaje, origen) in frags
    ]

    # 4. Generar respuesta con Gemini
    rag_response = generate_answer_with_references_gemini(frags_dict, query_text)

    # 5. Mostrar la respuesta final
    print("\n--- Respuesta generada por Gemini ---")
    print(rag_response["answer"])
    print("\n--- Referencias ---")
    for ref in rag_response["references"]:
        print(f" * {ref}")
    print(f"\n(Tiempo Gemini: {rag_response['gemini_time_seconds']:.2f} segundos)\n")


if __name__ == "__main__":
    main()
