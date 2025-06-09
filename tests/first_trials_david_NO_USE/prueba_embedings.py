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
from backend.app.services.retriever import retrieve_fragments


def main():
    query = "How do payments work?"
    k = 3
    results = retrieve_fragments(query, k=k)
    for idx, (text, score, source) in enumerate(results, start=1):
        print(f"{idx}. (score={score:.3f}) from {source}:\n{text}\n{'-'*40}\n")


if __name__ == "__main__":
    main()
