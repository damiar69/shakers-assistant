# Shakers AI Assistant

**An Intelligent Technical Support System with Personalized Recommendations**

This repository provides a full-featured solution for the Shakers platform:

1. **RAG Query Service**  
   - Answers user questions by retrieving relevant passages from a Markdown-based knowledge base.  
   - Uses OpenAI embeddings, a Chroma vector store, and Google Gemini to generate natural, concise answers with citations.

2. **Personalized Recommendation Service**  
   - Builds a dynamic profile per user from their query history.  
   - Suggests 2–3 new resources (articles, tutorials) for each query, ensuring topic diversity and clear explanations.

3. **Comprehensive Test Suite**  
   - **Unit Tests** for core logic (indexing, retrieval, recommendation).  
   - **Integration Tests** for FastAPI endpoints with mocks.  
   - **End-to-End Tests** running real queries against your API using JSON fixtures.

4. **Batch Evaluation Script** (`evaluation/evaluate.py`)  
   - Automates measurement of key metrics: total queries, overlap, recall, recommendation count, and diversity.  
   - Produces `metrics_summary.json` for downstream reporting and dashboards.

5. **Interactive Metrics Dashboard** (`front/metrics.py`)  
   - A Streamlit application visualizing RAG and recommendation KPIs in a branded, responsive UI.

---

##  Repository Layout

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

## ⚙️ Installation & Setup

1. **Clone** the repository:
   ```bash
   git clone <URL>
   cd shakers-case-study
   ```

2. Create & activate a virtual environment
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. Install Python dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variable
   ```bash
   cp .env.example .env
   ```
   Edit  `.env`  with your API keys

---

##  Running the Application

### Backend

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
  - POST `/rag/query`
  - POST `/recs/personalized`
  - GET `/metrics/summary`

###  Testing & Batch Evaluation

```bash
pytest --maxfail=1 -v -r a
```

### Batch Evaluation
bash
Copy


```bash
python evaluation/evaluate.py
```

Genera `evaluation/metrics_summary.json` con las métricas.

### Metrics Dashboard

```bash
streamlit run front/dashboard.py
```

Abre http://localhost:8501 para ver KPI de RAG y Recs.

---

## Metrics Definitions

- **RAG**:
  - Total Queries
  - Avg Overlap (% of ideal-answer keywords present in the generated answer) 
  - Avg Recall ( % of expected references correctly included in the response) 
- **Recs**:
  - Total Users 
  - Avg Recommendations (Average number of resources suggested per user. Calculated as:avg_recs = sum(len(recs_i) for each user i) / total_users)
  - Recommendation Diversity (Measures how many of those suggestions are unique)

---

**By dmiralles** 
