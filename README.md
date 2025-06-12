# Shakers AI Assistant

**An Intelligent Technical Support System with Personalized Recommendations**

This repository provides a full-featured solution for the Shakers platform:

1. **RAG Query Service**  
   - What it does: Answers user questions like “How do payments work?” by pulling in-scope text from a Markdown knowledge base.
   - How it works:
        Embeddings: Converts both query and docs into vectors via OpenAI.
        Retrieval: Finds the top-k most relevant chunks in Chroma.
        Generation: Feeds those snippets + the user’s question into Google Gemini to produce a concise answer with sources.

2. **Personalized Recommendation Service**  
   - What it does: After each query, suggests 2–3 fresh articles or tutorials tailored to the user’s past interests.
   - How it works:
        Builds a profile vector by averaging embeddings of documents the user has already seen.
        Embeds the current query.
        Scores all unseen docs by a weighted sum of “profile similarity” and “query similarity.”
        Returns the top 2–3 with the reason (distance cosine similarity of documents  that the user has consulted between documents that the user has not seen)

3. **Comprehensive Test Suite**  
   - **Unit Tests**  Validate core algorithms (index splitting, vector retrieval, recommendation ranking).
   - **Integration Tests**  Spin up FastAPI endpoints with mocked services to confirm JSON input/output. 
   - **End-to-End Tests** : Fire real requests against your running API using simulated question & profile JSON files; check for minimum overlap, correct 
                            references, and recommendation diversity.

4. **Batch Evaluation Script** (`evaluation/evaluate.py`)  
   - What it does: Runs through all test questions and profiles in one go, measuring:
        Overlap (how many ideal-answer keywords appear in the actual answer).
        Recall (fraction of expected doc references returned).
        Recommendation counts and diversity.


5. **Interactive Metrics Dashboard** (`front/metrics.py`)  
   - What it does: Presents your KPIs in a clean, branded Streamlit UI:
        RAG: total queries, avg overlap %, avg recall %.
        Recs: total users, avg recommendations per user, % unique recommendations.
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
├── .env ( create your with the api key.For Open AI use the one you have attached at the end of the document) 
├── requirements.txt
└── README.md
```

---

##  Installation & Setup

1. **Clone** the repository:
   ```bash
   git clone https://github.com/damiar69/shakers-assistant.git
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

 Create a `.env`  with your API keys

5. Run the script:  backend/app/services/retriever_openai.py to create the Chrome Vector BBDD

---

##  Running the Application

### Deploy the app

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
  - POST `/rag/query`
  - POST `/recs/personalized`
  - GET `/metrics/summary`
 
- Execute in another terminal:

```bash
   streamlit run front/streamlit_app.py
```

###  Testing & Batch Evaluation

```bash
pytest --maxfail=1 -v -r a
```

### Batch Evaluation


```bash
python evaluation/evaluate.py
```

Will generate `evaluation/metrics_summary.json` with some metrics for the dasboard using test/simulated_data.

#### Metrics Dashboard

- Execute in another terminal:
  
```bash
streamlit run front/metrics.py
```
---

#### Metrics Definitions

- **RAG**:
  - Total Queries
  - Avg Overlap (% of ideal-answer keywords present in the generated answer) 
  - Avg Recall ( % of expected references correctly included in the response) 
- **Recs**:
  - Total Users 
  - Avg Recommendations (Average number of resources suggested per user. Calculated as:avg_recs = sum(len(recs_i) for each user i) / total_users)
  - Recommendation Diversity (Measures how many of those suggestions are unique)

---

If you have any problems or questions, you can contact me at any time (+34 601147490) 

Imnot sure if you have API key for OPEN AI, if not use that one: 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
Is for test, i will delete it after the trial.

**By dmiralles** 
