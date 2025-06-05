# dashboard/streamlit_app.py

import os
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Shakers AI Assistant", page_icon="🤖", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# BACKEND URL (modifica si tu FastAPI no está en localhost:8000)
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("SHAKERS_BACKEND_URL", "http://localhost:8000")

# ─────────────────────────────────────────────────────────────────────────────
# CSS PERSONALIZADO
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .container{max-width:900px;margin:auto;padding:0 16px;}

    /* Input + botón */
    .input-area{display:flex;gap:8px;margin:16px 0;}
    .input-area .stTextInput>div{flex:1;}
    .send-button{background:#007BFF;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:.95rem;cursor:pointer;}
    .send-button:hover{background:#0056b3;}

    /* Burbuja de respuesta */
    .answer-bubble{background:#F1F3F5;padding:14px 18px;border-radius:12px;max-width:75%;
                   line-height:1.4;font-size:.95rem;margin-bottom:6px;}
    .refs{font-size:.85rem;margin-left:18px;color:#555;}

    /* Bloque de recomendaciones */
    .recs-block{background:#E8F0FE;border-left:4px solid #4285F4;padding:12px 18px;border-radius:6px;max-width:80%;margin-bottom:12px;}
    .recs-block h3{margin:0 0 8px 0;font-size:1rem;color:#333;}
    .recs-block ul{padding-left:20px;margin:0;font-size:.9rem;color:#444;}

    /* Historial de chat */
    .card{background:#fff;border-radius:8px;padding:16px 20px;margin-bottom:20px;
          box-shadow:0 4px 12px rgba(0,0,0,.05);}

    /* Logout button */
    .logout-button{background:#DC3545;color:#fff;border:none;border-radius:6px;padding:6px 14px;font-size:.9rem;cursor:pointer;margin-top:8px;}
    .logout-button:hover{background:#a71d2a;}

    /* Username input */
    .username-input .stTextInput>div{max-width:60%;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INICIALIZACIÓN
# ─────────────────────────────────────────────────────────────────────────────
if "username" not in st.session_state:
    st.session_state.username = ""  # Cadena vacía = no logueado

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Lista de { "q":..., "a":..., "refs":[...] }

if "current_a" not in st.session_state:
    st.session_state.current_a = ""

if "current_refs" not in st.session_state:
    st.session_state.current_refs = []

if "recs_history" not in st.session_state:
    st.session_state.recs_history = (
        []
    )  # Lista de recomendaciones: { "doc":..., "reason":... }


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────────────────────────────────────
def strip_inline_refs(text: str) -> str:
    """
    Elimina todo texto a partir de la primera aparición de "References:" (mayús o minús)
    para evitar duplicar la sección de referencias.
    """
    idx = text.lower().find("references:")
    return text if idx == -1 else text[:idx].rstrip()


def handle_login():
    """
    Callback que se ejecuta cuando el usuario hace clic en el botón 'Login'.
    Guarda el valor de 'input_username' en 'st.session_state.username' y limpia el historial.
    """
    user = st.session_state.input_username.strip()
    if not user:
        st.warning("Please enter a valid username.")
        return
    st.session_state.username = user
    st.session_state.chat_history = []
    st.session_state.current_a = ""
    st.session_state.current_refs = []
    st.session_state.recs_history = []


def handle_logout():
    """
    Callback para el botón 'Logout': reinicia todos los estados y vuelve a la pantalla de login.
    """
    st.session_state.username = ""
    st.session_state.chat_history = []
    st.session_state.current_a = ""
    st.session_state.current_refs = []
    st.session_state.recs_history = []


def handle_send():
    """
    Callback para el botón 'Send': envía la pregunta al endpoint /rag/query,
    guarda la respuesta y las referencias, actualiza el historial y luego
    solicita también recomendaciones al endpoint /recs/personalized.
    """
    q = st.session_state.input_question.strip()
    if not q:
        return

    # ─────────────────────────────────────────────────────────────────────────
    # 1) LLAMADA A /rag/query
    # ─────────────────────────────────────────────────────────────────────────
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
        answer = "Error: Could not contact RAG service."
        refs = []

    # Guardamos en el estado actual
    st.session_state.current_a = answer
    st.session_state.current_refs = refs

    # Añadimos al historial completo
    st.session_state.chat_history.append({"q": q, "a": answer, "refs": refs})

    # ─────────────────────────────────────────────────────────────────────────
    # 2) LLAMADA A /recs/personalized PARA OBTENER RECOMENDACIONES
    # ─────────────────────────────────────────────────────────────────────────
    payload_recs = {"user_id": st.session_state.username, "current_query": q}
    try:
        recs_resp = requests.post(
            f"{BACKEND_URL}/recs/personalized", json=payload_recs, timeout=8
        )
        recs_resp.raise_for_status()
        recs_data = recs_resp.json().get("recommendations", [])
    except requests.exceptions.HTTPError:
        # Si devuelve 404 (endpoint no implementado aún), devolvemos lista vacía
        recs_data = []
    except Exception:
        recs_data = []

    st.session_state.recs_history = recs_data

    # ─────────────────────────────────────────────────────────────────────────
    # 3) LIMPIAR EL CAMPO DE PREGUNTA
    # ─────────────────────────────────────────────────────────────────────────
    st.session_state.input_question = ""


# ─────────────────────────────────────────────────────────────────────────────
# PANTALLA DE LOGIN (SI NO HAY 'username')
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.username:
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.markdown("# 🤖 Shakers AI Assistant")
    st.markdown(
        "Enter your username to start.  \n"
        "Once logged in, you can ask technical questions about **Shakers**, "
        "see a clear answer with cited references, and consult your own history."
    )
    st.markdown("---")

    with st.container():
        st.markdown('<div class="username-input">', unsafe_allow_html=True)
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
    st.stop()  # Cortamos la ejecución aquí mientras no haya usuario logueado


# ─────────────────────────────────────────────────────────────────────────────
# PANTALLA PRINCIPAL (YA LOGUEADO)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='container'>", unsafe_allow_html=True)
st.markdown("# 🤖 Shakers AI Assistant")
st.markdown(
    f"Welcome, **{st.session_state.username}**!  \n"
    "Ask any technical question about **Shakers** below.  \n"
    "You’ll get a clear answer with cited references, and you can review your full history."
)
st.markdown("---")

# Botón de Logout (alineado a la derecha)
with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("")  # espacio vacío para mantener la columna
    with col2:
        if st.button("Logout", on_click=handle_logout, use_container_width=False):
            pass

# ─────────────────────────────────────────────────────────────────────────────
# ÁREA DE PREGUNTA / RESPUESTA
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
with st.container():
    st.markdown('<div class="input-area">', unsafe_allow_html=True)

    st.text_input(
        label="Type your question here",
        placeholder="Type your question here...",
        key="input_question",
        label_visibility="collapsed",
    )
    if st.button("Send", on_click=handle_send, use_container_width=False):
        pass

    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# BURBUJA DE RESPUESTA ÚNICA
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.current_a:
    clean_answer = strip_inline_refs(st.session_state.current_a)
    st.markdown(
        f'<div class="answer-bubble"><strong>Answer:</strong><br>{clean_answer}</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.current_refs:
        refs_html = "<br>".join(f"• {r}" for r in st.session_state.current_refs)
        st.markdown(
            f'<div class="refs">References:<br>{refs_html}</div>',
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE DE RECOMENDACIONES
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.recs_history:
    st.markdown("---")
    st.markdown("## 🎯 Personalized Recommendations")
    # Cada recomendación irá dentro de un <div> con clase .recs-block para estilo
    for rec in st.session_state.recs_history:
        doc_name = rec.get("doc", "")
        reason = rec.get("reason", "")
        st.markdown(
            f'<div class="recs-block">'
            f"<h3>• {doc_name}</h3>"
            f'<p style="margin:0;margin-left:12px;font-size:.9rem;color:#444;">{reason}</p>'
            f"</div>",
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# HISTORIAL DE CHAT (MUESTRA TODAS LAS PREGUNTAS/RESPUESTAS ANTERIORES)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.chat_history:
    st.markdown("---")
    st.markdown("## 💬 Chat History")
    for idx, entry in enumerate(st.session_state.chat_history, 1):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"**{idx}. Question:**  \n> {entry['q']}")
        st.markdown("---")
        ans_clean = strip_inline_refs(entry["a"])
        st.markdown(f"**Answer:**  \n{ans_clean}")
        if entry["refs"]:
            refs_html = "<br>".join(f"• {r}" for r in entry["refs"])
            st.markdown(
                f'<div class="refs">References:<br>{refs_html}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("dmiralles AI Assistant")
st.markdown("</div>", unsafe_allow_html=True)
