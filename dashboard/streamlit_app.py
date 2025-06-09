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
# INJECT CUSTOM CSS PARA DISEÑO “VERDE PROFUNDO” ELEGANTE
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* 1) Fondo principal: degradado verde + texto claro */
    html, body, .stApp {
        margin: 0; padding: 0;
        background: linear-gradient(180deg, #0a2b10 0%, #14421f 80%) !important;
        color: #e6f0e8 !important;
    }
    div[data-testid="stAppViewContainer"] > .main,
    div[data-testid="stSidebarNav"],
    div[data-testid="stToolbar"],
    [class*="css-vgazjp"] {
        background-color: transparent !important;
    }
    footer.st-krEhIo, #MainMenu {
        visibility: hidden !important;
    }

    /* 2) Contenedor general */
    .container {
        max-width: 900px;
        margin: auto;
        padding: 32px 24px 48px 24px;
        background-color: transparent !important;
    }
    .divider {
        border: none;
        border-top: 1px solid #2f5b3f !important;
        margin: 20px 0 28px 0;
    }

    /* 3) Cabecera */
    .header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .header-left { display: flex; flex-direction: column; }
    .header-title {
        font-size: 2.6rem;
        color: #ffffff;
        margin: 0;
        font-weight: 700;
    }
    .header-subtitle {
        font-size: 1rem;
        color: #b2ccb6;
        margin: 6px 0 0 0;
    }

    /* 3.1) Botones Login/Logout/Send */
    .login-button, .logout-button, .send-button {
        background-color: #c3dc62 !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        padding: 10px 22px !important;
        cursor: pointer !important;
        transition: background-color 0.2s ease !important;
    }
    .logout-button { padding: 8px 18px !important; }
    .login-button, .logout-button, .send-button { color: #333333 !important; }
    .login-button:hover, .logout-button:hover, .send-button:hover {
        background-color: #b0c54f !important;
        color: #000000 !important;
    }
    /* fuerza color interno de Streamlit */
    .login-button > div, .login-button > span,
    .logout-button > div, .logout-button > span,
    .send-button > div, .send-button > span {
        color: #333333 !important;
        opacity: 1 !important;
    }
    .login-button:hover > div, .logout-button:hover > div, .send-button:hover > div,
    .login-button:hover > span, .logout-button:hover > span, .send-button:hover > span {
        color: #000000 !important;
    }

    /* 4) Login Box */
    .login-box {
        background-color: rgba(255,255,255,0.06) !important;
        border-radius: 12px !important;
        padding: 28px 32px !important;
        margin: 60px 0 !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.25) !important;
    }
    .login-title { font-size: 1.8rem; color: #e6f0e8; margin-bottom: 6px; font-weight: 600; }
    .login-subtext { font-size: 1rem; color: #b2ccb6; margin-bottom: 14px; }
    .login-input .stTextInput > div { max-width: 60% !important; }

    /* 5) Chat Input */
    .chat-input-area {
        display: flex; gap: 12px; margin-bottom: 32px;
    }
    .chat-input-area .stTextInput > div { flex: 1 !important; }
    .chat-input-area input {
        background-color: #f2f8f3 !important;
        color: #0a2b10 !important;
        border: 1px solid #b2ccb6 !important;
        border-radius: 6px !important;
        padding: 10px 14px !important;
        font-size: 1rem !important;
    }

    /* 6) Burbuja de respuesta */
    .answer-container {
        background-color: #11421f !important;
        border-radius: 14px !important;
        padding: 20px 24px !important;
        max-width: 80%;
        font-size: 1rem;
        line-height: 1.6;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
        color: #f2f8f3 !important;
    }
    .answer-container strong { display: block; color: #c3dc62 !important; margin-bottom: 8px; font-size: 1.1rem; }

    /* 7) Referencias */
    .refs {
        font-size: 0.9rem; color: #a0c0a1;
        margin: 12px 0 0 16px; line-height: 1.4;
    }

    /* 8) Panel “Personalized Recommendations” */
    button.streamlit-expanderHeader {
        font-size: 2rem !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    .streamlit-expanderContent {
        background-color: #e8f6e8 !important;
        border-radius: 10px !important;
        padding: 16px 20px !important;
    }
    .recs-block {
        background-color: #f2faf2 !important;
        border-left: 4px solid #c3dc62 !important;
        padding: 16px 20px !important;
        border-radius: 8px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1) !important;
    }
    .recs-block h4 { margin: 0; font-size: 1rem; color: #0a2b10; font-weight: 600; }
    .recs-block p { margin: 6px 0 0 12px; font-size: 0.9rem; color: #2f5b3f; line-height: 1.5; }

    /* 9) Panel “Chat History” */
    button.streamlit-expanderHeader[aria-label*="Chat History"] {
        font-size: 2rem !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    .history-card {
        background-color: #f2faf2 !important;
        border-radius: 8px !important;
        padding: 16px 18px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }
    .history-card h5 {
        color: #c3dc62 !important;
        font-size: 1.6rem !important;
        font-weight: 700;
    }
    .history-card p { margin: 6px 0 0 0; font-size: 0.95rem; color: #0a2b10; line-height: 1.5; }
    .history-card .refs {
        font-size: 0.85rem; color: #2f5b3f;
        margin: 8px 0 0 12px; line-height: 1.4;
    }

    /* 10) Footer */
    .footer-text {
        font-size: 0.85rem; color: #a0c0a1;
        text-align: center; margin: 32px 0 12px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE: para login + chat + recomendaciones
# ─────────────────────────────────────────────────────────────────────────────
if "username" not in st.session_state:
    st.session_state.username = ""  # Usuario no autenticado → mostrar login

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

    # 1) Llamamos a /rag/query
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

    # Añadimos al historial completo
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

    # 3) Limpiamos el campo de input
    st.session_state.input_question = ""


# ─────────────────────────────────────────────────────────────────────────────
# 1) PANTALLA DE LOGIN (si no hay user en session_state)
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.username:
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="login-box">
          <h2 class="login-title">🤖 Shakers AI Assistant</h2>
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
    st.stop()  # No mostramos nada más hasta que se haga login


# ─────────────────────────────────────────────────────────────────────────────
# 2) PANTALLA PRINCIPAL (USUARIO LOGUEADO)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='container'>", unsafe_allow_html=True)

# 2.1) Cabecera con Título + subtítulo, y botón Logout a la derecha
st.markdown(
    """
    <div class="header-row">
      <div class="header-left">
        <h1 class="header-title">🤖 Shakers AI Assistant</h1>
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

# Botón Logout alineado a la derecha
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

# 2.3) Burbuja de respuesta única (reemplazada cada vez que se envía algo nuevo)
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
    with st.expander("🎯 Personalized Recommendations"):
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
    with st.expander("💬 Chat History"):
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
                  <p style="margin-left:10px; color: #0a2b10;">{question}</p>
                  <p style="margin-top:8px; color: #0a2b10;"><strong>Answer:</strong> {answer}</p>
                  {f'<div class="refs">References:<br>{refs_html}</div>' if refs_html else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# 2.6) Footer
st.markdown(
    """
      <p class="footer-text"> dmiralles AI Assistant</p>
      </div>  <!-- fin de .container -->
    """,
    unsafe_allow_html=True,
)
