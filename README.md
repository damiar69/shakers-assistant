# Shakers AI Assistant

**Intelligent Technical Support System with Personalized Recommendations**

Este proyecto implementa:

1. **RAG Query Service**: responde preguntas basadas en una base de conocimiento Markdown usando OpenAI embeddings + Chroma + LLM Gemini.
2. **Personalized Recommendation Service**: sugiere 2–3 recursos basados en el historial de consultas del usuario.
3. **Suite de Tests**: unitarios, integración y E2E que validan indexación, recuperación, generación y recomendaciones con datos simulados y reales.
4. **Batch Evaluation**: script (`evaluation/evaluate.py`) que mide overlap, recall y métricas de recomendaciones en lote.
5. **Dashboard de Métricas**: app en Streamlit (`front/dashboard.py`) para visualizar KPIs de RAG y Recs.

---

##  Estructura del Repositorio

```
shakers-case-study/
├── backend/app/
│   ├── main.py            # FastAPI + routers: /rag, /recs, /metrics
│   ├── routers/
│   │   ├── rag.py
│   │   ├── recs.py
│   │   └── metrics.py
│   ├── services/retriever_openai.py
│   │   ├── retriever_openai.py
│   │   ├── llm_gemini.py
│   │   └── recommendations.py
│   └── db.py             # SQLite init 
├── data/
│   ├── kb/               # Documents on .md
│   ├── chroma_db/
│   └── embed_cache/
│   └── doc_embeddings.json
│   └── shakers.db
├── evaluation/
│   ├── evaluate.py       # Creates metrics_summary.json 
│   └── metrics_summary.json
├── front/
│   ├── logo.png
│   ├── streamlit_app.py  # Chat UI (RAG + recs)
│   └── metrics.py #Dashboard of metrics creted on evaluate.py
├── tests/
│   ├── simulated_data/
│   │   ├── test_questions.json
│   │   └── user_profiles.json
│   ├── conftest.py
│   ├── test_retriever.py
│   ├── test_recs.py
│   ├── test_api.py
│   ├── test_eval_rag.py
│   └── test_eval_recs.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚙️ Instalación

1. Clona el repositorio:
   ```bash
   git clone <URL>
   cd shakers-case-study
   ```

2. Crea y activa entorno virtual:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Copia el ejemplo de variables de entorno:
   ```bash
   cp .env.example .env
   ```
   Rellena `.env` con tus claves OpenAI y Google.

---

## 🚀 Ejecutar la Aplicación

### Backend

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
  - POST `/rag/query`
  - POST `/recs/personalized`
  - GET `/metrics/summary`

### Tests

```bash
pytest --maxfail=1 -v -r a
```

### Evaluación Batch

```bash
python evaluation/evaluate.py
```

Genera `evaluation/metrics_summary.json` con las métricas.

### Dashboard de Métricas

```bash
streamlit run front/dashboard.py
```

Abre http://localhost:8501 para ver KPI de RAG y Recs.

---

## 📈 Métricas Explicadas

- **RAG**:
  - Total Queries
  - Avg Overlap (% de palabras clave)
  - Avg Recall (% de referencias citadas)
- **Recs**:
  - Total Users evaluados
  - Avg Recommendations (media de sugerencias)
  - Recommendation Diversity (% recursos únicos)

---

**By [David Miralles]**
