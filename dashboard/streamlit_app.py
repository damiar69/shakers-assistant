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
)

# ─────────────────────────────────────────────────────────────────────────────
# INJECT CUSTOM CSS FOR CHAT BUBBLES AND LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Container around entire chat */
    .chat-container {
        max-width: 800px;
        margin: auto;
        padding: 0 16px;
    }
    /* Each message bubble */
    .assistant-msg, .user-msg {
        padding: 12px 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        line-height: 1.4;
        font-size: 0.95rem;
        max-width: 70%;
        word-wrap: break-word;
    }
    /* Assistant bubble (left side, gray background) */
    .assistant-container {
        display: flex;
        justify-content: flex-start;
    }
    .assistant-msg {
        background-color: #F1F3F5;
        color: #000;
    }
    /* References under assistant message */
    .assistant-refs {
        font-size: 0.85rem;
        margin-left: 16px;
        color: #555;
    }
    /* User bubble (right side, green background) */
    .user-container {
        display: flex;
        justify-content: flex-end;
    }
    .user-msg {
        background-color: #DCF8C6;
        color: #000;
    }
    /* Scrollable history box */
    .history-box {
        max-height: 60vh;
        overflow-y: auto;
        padding-right: 8px;
        margin-bottom: 16px;
    }
    /* Input area sits above history */
    .input-area {
        margin-top: 16px;
        margin-bottom: 8px;
        display: flex;
        gap: 8px;
    }
    .input-area .stTextInput > div {
        flex: 1;
    }
    .send-button {
        background-color: #007BFF;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 0.95rem;
        cursor: pointer;
    }
    .send-button:hover {
        background-color: #0056b3;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
st.markdown("# 🤖 Shakers AI Assistant")
st.markdown(
    """
    Welcome to the interactive Shakers AI Assistant.  
    Ask any technical question about the Shakers platform below and receive  
    a clear, cited response (and—soon—personalized recommendations).
    """
)

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND URL
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("SHAKERS_BACKEND_URL", "http://localhost:8000")

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = (
        []
    )  # Lista de dicts: {sender:"user"/"assistant", text:str, refs:[str]}


# ─────────────────────────────────────────────────────────────────────────────
# DEFINE CALLBACK PARA EL BOTÓN “SEND”
# ─────────────────────────────────────────────────────────────────────────────
def handle_send():
    """
    Esta función se ejecuta cuando el usuario hace clic en el botón Send.
    1) Lee st.session_state.input_question
    2) Agrega el mensaje a chat_history
    3) Llama a /rag/query y agrega la respuesta
    4) Limpia st.session_state.input_question
    """
    user_q = st.session_state.input_question.strip()
    if not user_q:
        # Si no hay texto, no hacemos nada
        return

    # 1) Agregar mensaje del usuario
    st.session_state.chat_history.append({"sender": "user", "text": user_q, "refs": []})

    # 2) Llamar a /rag/query
    payload = {"user_id": "anonymous", "query": user_q}
    try:
        resp = requests.post(f"{BACKEND_URL}/rag/query", json=payload, timeout=8)
        resp.raise_for_status()
        rag_data = resp.json()
        answer = rag_data.get("answer", "")
        refs = rag_data.get("references", [])
    except Exception:
        answer = "⚠️ Error: Could not contact RAG service."
        refs = []

    # 3) Agregar respuesta del asistente
    st.session_state.chat_history.append(
        {"sender": "assistant", "text": answer, "refs": refs}
    )

    # 4) Limpiar el campo de entrada
    st.session_state.input_question = ""


# ─────────────────────────────────────────────────────────────────────────────
# INPUT AREA (QUESTION + SEND BUTTON)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
with st.container():
    st.markdown('<div class="input-area">', unsafe_allow_html=True)

    # Campo de texto para la pregunta
    user_question = st.text_input(
        label="Type your question here",
        placeholder="Type your question here...",
        key="input_question",
        label_visibility="collapsed",
    )

    # Botón “Send” que llama a handle_send
    st.button(
        "Send",
        key="send_button",
        help="Click to ask your question",
        on_click=handle_send,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CHAT HISTORY (SCROLLABLE)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="history-box">', unsafe_allow_html=True)
for entry in st.session_state.chat_history:
    sender = entry["sender"]
    text = entry["text"]
    if sender == "assistant":
        st.markdown('<div class="assistant-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="assistant-msg">{text}</div>', unsafe_allow_html=True)
        if entry.get("refs"):
            ref_lines = "<br>".join(f"• {r}" for r in entry["refs"])
            st.markdown(
                f'<div class="assistant-refs">References:<br>{ref_lines}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="user-container">', unsafe_allow_html=True)
        st.markdown(f'<div class="user-msg">{text}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("© 2025 Shakers AI Assistant")
st.markdown("</div>", unsafe_allow_html=True)
