import os
import sys

# 1) Calculamos la ruta absoluta de la carpeta raíz del proyecto
#    Este script está en: shakers-case-study/tests/prueba_embedings.py
#    Subimos dos niveles para llegar a shakers-case-study/
PROJECT_ROOT = os.path.abspath(os.path.join(__file__, os.pardir, os.pardir))
# PROJECT_ROOT apunta ahora a C:\Users\ddol\Desktop\shakers-case-study

# 2) Añadimos esa carpeta al comienzo de sys.path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 3) Ahora Python sabrá encontrar backend.app.services.retriever
from backend.app.services.retriever_openai import retrieve_fragments_openai


def main():
    query_text = "How do payments work?"
    k_results = 3
    frags = retrieve_fragments_openai(query_text, k=k_results)
    print(f"\nQuery: {query_text}\nTop {k_results} fragments:\n")
    for idx, (text, score, source) in enumerate(frags, start=1):
        print(f"{idx}. (score={score:.3f}) from {source}:\n{text}\n{'-'*40}\n")


if __name__ == "__main__":
    main()
