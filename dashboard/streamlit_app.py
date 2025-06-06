# dashboard/streamlit_app.py

import os
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT PAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Shakers AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND URL (ajusta si tu FastAPI no está en localhost:8000)
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("SHAKERS_BACKEND_URL", "http://localhost:8000")

# ─────────────────────────────────────────────────────────────────────────────
# INJECT CUSTOM CSS PARA DISEÑO ELEGANTE Y LEGIBLE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ===========================
       0) LOGO DE EMPRESA COMO FONDO HEADER
       =========================== */
    .logo-header {
        background: url('https://your-company.com/path/to/logo.png') no-repeat left center;
        background-size: 40px 40px;
        padding-left: 56px;
    }

    /* ===========================
       1) FONDO GLOBAL VERDE CLARO
       =========================== */
    html, body, [class*="css"] {
        background-color: #f0faf2 !important;
        color: #0a170c !important;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* ===========================
       2) CONTENEDOR PRINCIPAL
       =========================== */
    .container {
        max-width: 900px;
        margin: auto;
        padding: 24px 24px 40px 24px;
        background-color: transparent;
    }
    .divider {
        border: none;
        border-top: 1px solid #c4dcc4;
        margin: 16px 0 24px 0;
    }

    /* ===========================
       3) CABECERA + LOGOUT
       =========================== */
    .header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .header-left {
        display: flex;
        flex-direction: column;
    }
    .header-title {
        font-size: 2.4rem;
        color: #0a170c;
        margin: 0;
        font-weight: 700;
    }
    .header-subtitle {
        font-size: 1rem;
        color: #47654a;
        margin-top: 4px;
        margin-bottom: 0;
    }
    .logout-button {
        background-color: #ffcc00;
        color: #0a170c;
        border: none !important;
        border-radius: 6px;
        padding: 6px 16px;
        font-size: 0.95rem;
        font-weight: 500;
        cursor: pointer;
    }
    .logout-button:hover {
        background-color: #e6b800;
    }

    /* ===========================
       4) PANTALLA DE LOGIN
       =========================== */
    .login-box {
        background-color: rgba(255, 255, 255, 0.6);
        border-radius: 10px;
        padding: 24px 32px;
        margin-top: 60px;
        margin-bottom: 60px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    .login-title {
        font-size: 1.8rem;
        color: #0a170c;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .login-subtext {
        font-size: 1rem;
        color: #47654a;
        margin-bottom: 16px;
    }
    .login-input .stTextInput > div {
        max-width: 70%;
    }
    .login-button {
        background-color: #ffcc00;
        color: #0a170c;
        border: none !important;
        border-radius: 6px;
        padding: 10px 20px;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
    }
    .login-button:hover {
        background-color: #e6b800;
    }

    /* ===========================
       5) ÁREA DE PREGUNTA + BOTÓN SEND
       =========================== */
    .chat-input-area {
        display: flex;
        gap: 12px;
        margin-bottom: 28px;
    }
    .chat-input-area .stTextInput > div {
        flex: 1;
    }
    .send-button {
        background-color: #ffcc00;
        color: #0a170c;
        border: none !important;
        border-radius: 6px;
        padding: 10px 22px;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
    }
    .send-button:hover {
        background-color: #e6b800;
    }

    /* ===========================
       6) BURBUJA DE RESPUESTA CENTRAL
       =========================== */
    .answer-container {
        background-color: #1f402e;
        border-radius: 14px;
        padding: 20px 24px;
        max-width: 80%;
        line-height: 1.6;
        font-size: 1rem;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        color: #ffffff;  /* Texto blanco para alta legibilidad */
    }
    .answer-container strong {
        display: block;
        color: #ffcc00; /* “Answer:” en dorado */
        margin-bottom: 8px;
        font-size: 1.1rem;
    }

    /* ===========================
       7) REFERENCIAS DENTRO DE LA BURBUJA
       =========================== */
    .refs {
        font-size: 0.9rem;
        color: #c0d2c2;
        margin-top: 12px;
        margin-left: 16px;
        line-height: 1.4;
    }

    /* ===========================
       8) PANEL “RECOMMENDATIONS”
       =========================== */
    .streamlit-expanderHeader {
        color: #0a170c !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
    }
    .streamlit-expanderContent {
        background-color: #dbf0dd !important;
        border-radius: 8px !important;
        padding: 16px 20px !important;
    }
    .recs-block {
        background-color: #e6f4e9;
        border-left: 4px solid #ffcc00;
        padding: 14px 18px;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .recs-block h4 {
        margin: 0;
        font-size: 1rem;
        color: #0a170c;
        font-weight: 600;
    }
    .recs-block p {
        margin: 4px 0 0 10px;
        font-size: 0.9rem;
        color: #47654a;
        line-height: 1.5;
    }

    /* ===========================
       9) PANEL “CHAT HISTORY”
       =========================== */
    .history-card {
        background-color: #e6f4e9;
        border-radius: 8px;
        padding: 14px 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .history-card h5 {
        margin: 0;
        color: #ffcc00;
        font-size: 1rem;
        font-weight: 600;
    }
    .history-card p {
        margin: 6px 0 0 0;
        font-size: 0.95rem;
        color: #0a170c;
        line-height: 1.5;
    }
    .history-card .refs {
        font-size: 0.85rem;
        color: #0a170c;
        margin-top: 8px;
        margin-left: 12px;
        line-height: 1.4;
    }

    /* ===========================
       10) FOOTER
       =========================== */
    .footer-text {
        font-size: 0.85rem;
        color: #47654a;
        text-align: center;
        margin-top: 28px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE: para login + chat + recomendaciones
# ─────────────────────────────────────────────────────────────────────────────
if "username" not in st.session_state:
    st.session_state.username = ""  # Usuario vacío → mostramos login

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # [{"q": ..., "a": ..., "refs": [...]}]

if "current_a" not in st.session_state:
    st.session_state.current_a = ""

if "current_refs" not in st.session_state:
    st.session_state.current_refs = []

if "recs_history" not in st.session_state:
    st.session_state.recs_history = []  # [{"doc": ..., "reason": ...}]


# ─────────────────────────────────────────────────────────────────────────────
# AUXILIAR: eliminar texto duplicado desde “References:”
# ─────────────────────────────────────────────────────────────────────────────
def strip_inline_refs(text: str) -> str:
    """Elimina todo desde ‘References:’ en adelante."""
    idx = text.lower().find("references:")
    return text if idx == -1 else text[:idx].rstrip()


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK: handle_login()
# ─────────────────────────────────────────────────────────────────────────────
def handle_login():
    user = st.session_state.input_username.strip()
    if not user:
        st.warning("Please enter a valid username.")
        return
    st.session_state.username = user
    st.session_state.chat_history = []
    st.session_state.current_a = ""
    st.session_state.current_refs = []
    st.session_state.recs_history = []


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK: handle_logout()
# ─────────────────────────────────────────────────────────────────────────────
def handle_logout():
    st.session_state.username = ""
    st.session_state.chat_history = []
    st.session_state.current_a = ""
    st.session_state.current_refs = []
    st.session_state.recs_history = []


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK: handle_send()
# ─────────────────────────────────────────────────────────────────────────────
def handle_send():
    q = st.session_state.input_question.strip()
    if not q:
        return

    # 1) Llamada a /rag/query
    try:
        resp = requests.post(
            f"{BACKEND_URL}/rag/query",
            json={"user_id": st.session_state.username, "query": q},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("answer", "")
        refs = data.get("references", [])
    except Exception:
        answer = "⚠️ Error: Could not contact RAG service."
        refs = []

    # Guardamos la última respuesta
    st.session_state.current_a = answer
    st.session_state.current_refs = refs

    # Agregamos al historial completo
    st.session_state.chat_history.append({"q": q, "a": answer, "refs": refs})

    # 2) Llamada a /recs/personalized
    payload_recs = {"user_id": st.session_state.username, "current_query": q}
    try:
        recs_resp = requests.post(
            f"{BACKEND_URL}/recs/personalized", json=payload_recs, timeout=8
        )
        recs_resp.raise_for_status()
        recs_data = recs_resp.json().get("recommendations", [])
    except:
        recs_data = []
    st.session_state.recs_history = recs_data

    # 3) Limpiar el campo de input
    st.session_state.input_question = ""


# ─────────────────────────────────────────────────────────────────────────────
# 1) PANTALLA DE LOGIN (si no hay user en session_state)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.username:
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="login-box">
          <h2 class="login-title logo-header"> Shakers AI Assistant</h2>
          <p class="login-subtext">
            Enter your username to start. Once logged in, you can ask  
            technical questions about <strong>Shakers</strong>, see a clear  
            answer with cited references, and consult your own history.
          </p>
          <hr class="divider">
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown('<div class="login-input">', unsafe_allow_html=True)
        st.text_input(
            label="Enter your username",
            placeholder="Type your username here...",
            key="input_username",
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Login", on_click=handle_login, use_container_width=False):
            pass

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()  # Detenemos la ejecución hasta que se haga login


# ─────────────────────────────────────────────────────────────────────────────
# 2) PANTALLA PRINCIPAL (USUARIO LOGUEADO)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='container'>", unsafe_allow_html=True)

# 2.1) Cabecera con título + subtítulo, y botón Logout alineado a la derecha
st.markdown(
    """
    <div class="header-row">
      <div class="header-left logo-header">
        <h1 class="header-title"> Shakers AI Assistant</h1>
        <p class="header-subtitle">
          Welcome, <strong>"""
    + st.session_state.username
    + """</strong>!  
          Ask any technical question about <strong>Shakers</strong> below.
        </p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Botón Logout como Streamlit widget (alineado a la derecha)
col1, col2 = st.columns([8, 1])
with col1:
    st.write("")  # espacio vacío
with col2:
    if st.button("Logout", on_click=handle_logout, use_container_width=False):
        pass

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# 2.2) Área de input + botón Send
with st.container():
    st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)

    st.text_input(
        label="Type your question here",
        placeholder="Type your question here...",
        key="input_question",
        label_visibility="collapsed",
    )

    if st.button("Send", on_click=handle_send, use_container_width=False):
        pass

    st.markdown("</div>", unsafe_allow_html=True)

# 2.3) Burbuja de respuesta única (se reemplaza cada vez que se envía una nueva pregunta)
if st.session_state.current_a:
    answer_clean = strip_inline_refs(st.session_state.current_a)
    st.markdown(
        f"""
        <div class="answer-container">
          <strong>Answer:</strong>
          {answer_clean}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.current_refs:
        refs_html = "<br>".join(f"• {r}" for r in st.session_state.current_refs)
        st.markdown(
            f"""
            <div class="refs">
              References:<br>{refs_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

# 2.4) Panel “Personalized Recommendations” (colapsable)
if st.session_state.recs_history:
    with st.expander("🎯 Personalized Recommendations", expanded=False):
        for rec in st.session_state.recs_history:
            doc_name = rec.get("doc", "")
            reason = rec.get("reason", "")
            st.markdown(
                f"""
                <div class="recs-block">
                  <h4>• {doc_name}</h4>
                  <p>{reason}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# 2.5) Panel “Chat History” (colapsable, scrollable)
if st.session_state.chat_history:
    with st.expander("💬 Chat History", expanded=False):
        for idx, entry in enumerate(st.session_state.chat_history, 1):
            question = entry["q"]
            answer = strip_inline_refs(entry["a"])
            refs = entry.get("refs", [])
            refs_html = ""
            if refs:
                refs_html = "<br>".join(f"• {r}" for r in refs)

            st.markdown(
                f"""
                <div class="history-card">
                  <h5>{idx}. Question:</h5>
                  <p style="margin-left:10px; color: #0a170c;">{question}</p>
                  <p style="margin-top:8px; color: #0a170c;"><strong>Answer:</strong> {answer}</p>
                  {f'<div class="refs">References:<br>{refs_html}</div>' if refs_html else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# 2.6) Footer
st.markdown(
    """
      <p class="footer-text">© 2025 David AI Assistant</p>
      </div>  <!-- fin de .container -->
    """,
    unsafe_allow_html=True,
)
