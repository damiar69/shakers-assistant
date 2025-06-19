"""
Streamlit Frontend module for Shakers AI Assistant interface.

1. Full-page custom theming with CSS injected for a polished dark-green gradient look.
2. Base64‐encoded logo injection for self‐contained assets without external URLs.
3. Sidebar-free, wide‐layout chat UI with login, chat input, personalized recs, and history.
4. Session state management for username, chat history, current answer/refs, and recs.
5. Clear separation of handlers (login, logout, send) and UI sections (login screen vs main screen).
"""

import os
import base64
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 1) STREAMLIT PAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Shakers AI Assistant",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2) BACKEND URL
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("SHAKERS_BACKEND_URL", "http://localhost:8000")

# ─────────────────────────────────────────────────────────────────────────────
# 3) LOGO BASE64
# ─────────────────────────────────────────────────────────────────────────────
script_dir = os.path.dirname(__file__)
logo_path = os.path.join(script_dir, "logo.png")
with open(logo_path, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()

# ─────────────────────────────────────────────────────────────────────────────
# 4) INJECT CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <style>
    /* 1) Fondo degradado y contenedores transparentes */
    html, body, .stApp {{
      margin:0; padding:0;
      background: linear-gradient(180deg, #0a2b10 0%, #14421f 80%) !important;
      color: #e6f0e8 !important;
    }}
    div[data-testid="stAppViewContainer"] > .main,
    div[data-testid="stSidebarNav"],
    div[data-testid="stToolbar"],
    [class*="css-vgazjp"] {{
      background-color: transparent !important;
    }}
    footer.st-krEhIo, #MainMenu {{ visibility:hidden !important; }}

    /* 2) Reducir espacio superior */
    section.main > div.block-container {{ padding-top:0.5rem !important; }}
    .container {{ margin-top:0 !important; }}

    /* 3) Contenedor general */
    .container {{
      max-width:900px; margin:auto;
      padding:32px 24px 48px 24px;
      background-color:transparent !important;
    }}
    .divider {{
      border:none; border-top:1px solid #2f5b3f !important;
      margin:20px 0 28px 0;
    }}

    /* 4) Cabecera con logo */
    .header-row {{
      display:flex; justify-content:space-between;
      align-items:center; margin-bottom:8px;
    }}
    .header-left {{
      display:flex; align-items:center; gap:8px;
    }}
    .header-logo {{ width:40px; height:40px; }}
    .header-title {{
      font-size:2.6rem; color:#ffffff;
      margin:0; font-weight:700;
    }}
    .header-subtitle {{
      font-size:1rem; color:#b2ccb6;
      margin:4px 0 0 48px;
    }}

    /* 5) Botones */
    .login-button, .logout-button, .send-button {{
      background-color:#c3dc62 !important;
      color:#333333 !important;
      border:none !important; border-radius:6px !important;
      font-size:1rem !important; font-weight:500 !important;
      padding:10px 22px !important; cursor:pointer !important;
      transition:background-color .2s ease !important;
    }}
    .logout-button {{ padding:8px 18px !important; }}
    .login-button:hover, .logout-button:hover, .send-button:hover {{
      background-color:#b0c54f !important; color:#000 !important;
    }}
    .login-button > div, .login-button > span,
    .logout-button > div, .logout-button > span,
    .send-button > div, .send-button > span {{
      color:#333333 !important; opacity:1 !important;
    }}

    /* 6) Login Box */
    .login-box {{
      background:rgba(255,255,255,0.06) !important;
      border-radius:12px !important; padding:28px 32px !important;
      margin:60px 0 !important;
      box-shadow:0 4px 16px rgba(0,0,0,0.25) !important;
    }}
    .login-title {{ font-size:1.8rem;color:#e6f0e8;margin-bottom:6px;font-weight:600; }}
    .login-subtext {{ font-size:1rem;color:#b2ccb6;margin-bottom:14px; }}

    /* 7) Chat Input */
    .chat-input-area {{
      display:flex; gap:12px; margin-bottom:32px;
    }}
    .chat-input-area .stTextInput > div {{ flex:1 !important; }}
    .chat-input-area input {{
      background:#f2f8f3 !important; color:#0a2b10 !important;
      border:1px solid #b2ccb6 !important; border-radius:6px !important;
      padding:10px 14px !important; font-size:1rem !important;
    }}

    /* 8) Answer bubble */
    .answer-container {{
      background:#11421f !important; border-radius:14px !important;
      padding:20px 24px !important; max-width:80%; font-size:1rem;
      line-height:1.6; margin-bottom:16px;
      box-shadow:0 4px 12px rgba(0,0,0,0.2) !important;
      color:#f2f8f3 !important;
    }}
    .answer-container strong {{
      display:block;color:#c3dc62 !important;
      margin-bottom:8px;font-size:1.1rem;
    }}

    /* 9) Refs */
    .refs {{
      font-size:0.9rem;color:#a0c0a1;
      margin:12px 0 0 16px;line-height:1.4;
    }}

    /* 10) Expander headers */
    .streamlit-expanderHeader,
    .streamlit-expanderHeader * {{
      color:#ffffff !important;
      font-weight:700 !important;
    }}
    .streamlit-expanderContent {{
      background:#e8f6e8 !important;border-radius:10px !important;
      padding:16px 20px !important;
    }}

    /* 11) Card wrapper */
    .streamlit-expander {{
      border:1px solid #c3dc62 !important;
      border-radius:8px !important;
      margin-bottom:16px !important;
    }}
    .streamlit-expanderHeader {{
      background:transparent !important;
      padding:12px 16px !important;
    }}
    .streamlit-expanderContent {{
      background:#11421f !important;
      border-radius:0 0 8px 8px !important;
      padding:16px !important;
    }}

    /* 12) Recs blocks */
    .recs-block {{
      background:#1d553f !important; border-radius:8px !important;
      padding:12px 16px !important; margin-bottom:12px !important;
    }}
    .recs-block h4 {{
      margin:0 0 6px 0; font-size:1.1rem !important; color:#c3dc62 !important;
    }}
    .recs-block p {{
      margin:0; font-size:0.95rem !important; color:#e6f0e8 !important;
    }}

    /* 13) History cards */
    .history-card {{
      background:#1d553f !important; border-radius:8px !important;
      padding:12px 16px !important; margin-bottom:12px !important;
    }}
    .history-card h5 {{
      margin:0 0 8px 0; font-size:1.1rem !important; color:#c3dc62 !important;
    }}
    .history-card p {{
      margin:4px 0 !important; font-size:0.95rem !important; color:#e6f0e8 !important;
    }}

    /* 14) Card refs */
    .history-card .refs,
    .recs-block .refs {{
      margin-top:8px !important; font-size:0.9rem !important; color:#a0c0a1 !important;
    }}

    /* 15) Footer */
    .footer-text {{
      font-size:0.85rem; color:#a0c0a1;
      text-align:center; margin:32px 0 12px 0;
    }}

    /* 16) Agrandar solo esos dos expanders */
    button[aria-label^="Personalized Recommendations"],
    button[aria-label^="Chat History"] {{   /* doble llave de apertura */
      font-size: 2.2rem !important;
    }}                                         /* doble llave de cierre */
    button[aria-label^="Personalized Recommendations"] *,
    button[aria-label^="Chat History"] * {{  /* doble llave de apertura */
      font-size: inherit !important;
    }}                                         /* doble llave de cierre */
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# 5) SESSION STATE y HELPERS
# ─────────────────────────────────────────────────────────────────────────────
if "username" not in st.session_state:
    st.session_state.username = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_a" not in st.session_state:
    st.session_state.current_a = ""
if "current_refs" not in st.session_state:
    st.session_state.current_refs = []
if "recs_history" not in st.session_state:
    st.session_state.recs_history = []


def strip_inline_refs(text: str) -> str:
    idx = text.lower().find("references:")
    return text if idx == -1 else text[:idx].rstrip()


# ─────────────────────────────────────────────────────────────────────────────
# 6) HANDLERS
# ─────────────────────────────────────────────────────────────────────────────
def handle_login():
    u = st.session_state.input_username.strip()
    if u:
        st.session_state.username = u


def handle_logout():
    st.session_state.username = ""
    st.session_state.chat_history = []
    st.session_state.current_a = ""
    st.session_state.current_refs = []
    st.session_state.recs_history = []


def handle_send():
    q = st.session_state.input_question.strip()
    if not q:
        return
    # RAG query
    try:
        r = requests.post(
            f"{BACKEND_URL}/rag/query",
            json={"user_id": st.session_state.username, "query": q},
            timeout=8,
        )
        r.raise_for_status()
        data = r.json()
        answer = data.get("answer", "")
        refs = data.get("references", [])
    except:
        answer, refs = " Error: Could not contact RAG service.", []
    st.session_state.current_a = answer
    st.session_state.current_refs = refs
    st.session_state.chat_history.append({"q": q, "a": answer, "refs": refs})

    # Personalized recs
    try:
        recs = (
            requests.post(
                f"{BACKEND_URL}/recs/personalized",
                json={"user_id": st.session_state.username, "current_query": q},
                timeout=8,
            )
            .json()
            .get("recommendations", [])
        )
    except:
        recs = []
    st.session_state.recs_history = recs
    st.session_state.input_question = ""


# ─────────────────────────────────────────────────────────────────────────────
# 7) LOGIN SCREEN
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.username:
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="login-box">
          <div class="header-row">
            <div class="header-left">
              <img class="header-logo" src="data:image/png;base64,{logo_b64}" />
              <h1 class="login-title">Shakers AI Assistant</h1>
            </div>
          </div>
          <p class="login-subtext">
            Enter your username to start…
          </p>
          <hr class="divider">
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.text_input(
        "Username",
        key="input_username",
        placeholder="Type your username here...",
        label_visibility="collapsed",
    )
    st.button(
        "Login", on_click=handle_login, use_container_width=False, key="btn_login"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 8) MAIN SCREEN
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div class='container'>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div class='header-row'>
      <div class='header-left'>
        <img class='header-logo' src='data:image/png;base64,{logo_b64}'/>
        <h1 class='header-title'>Shakers AI Assistant</h1>
      </div>
      <div></div>
    </div>
    <p class='header-subtitle'>
      Welcome, <strong>{st.session_state.username}</strong>!
    </p>
    <hr class='divider'>
    """,
    unsafe_allow_html=True,
)
_, col2 = st.columns([8, 1])
with col2:
    st.button(
        "Logout", on_click=handle_logout, use_container_width=False, key="btn_logout"
    )

st.markdown("<div class='chat-input-area'>", unsafe_allow_html=True)
st.text_input(
    "Your question",
    key="input_question",
    placeholder="Type your question here...",
    label_visibility="collapsed",
)
st.button("Send", on_click=handle_send, use_container_width=False, key="btn_send")
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.current_a:
    clean = strip_inline_refs(st.session_state.current_a)
    st.markdown(
        f"<div class='answer-container'><strong>Answer:</strong> {clean}</div>",
        unsafe_allow_html=True,
    )
    if st.session_state.current_refs:
        refs_html = "<br>".join(f"• {r}" for r in st.session_state.current_refs)
        st.markdown(
            f"<div class='refs'>References:<br>{refs_html}</div>",
            unsafe_allow_html=True,
        )

if st.session_state.recs_history:
    with st.expander("Personalized Recommendations"):
        for rec in st.session_state.recs_history:
            st.markdown(
                f"<div class='recs-block'><h4>• {rec['doc']}</h4><p>{rec['reason']}</p></div>",
                unsafe_allow_html=True,
            )

if st.session_state.chat_history:
    with st.expander("Chat History"):
        for i, e in enumerate(st.session_state.chat_history, 1):
            q, a, refs = e["q"], strip_inline_refs(e["a"]), e["refs"]
            refs_html = "<br>".join(f"• {r}" for r in refs) if refs else ""
            refs_block = (
                f"<div class='refs'>References:<br>{refs_html}</div>"
                if refs_html
                else ""
            )
            st.markdown(
                f"<div class='history-card'>"
                f"<h5>{i}. Question:</h5>"
                f"<p style='margin-left:10px;color:#0a2b10;'>{q}</p>"
                f"<p style='margin-top:8px;color:#0a2b10;'><strong>Answer:</strong> {a}</p>"
                f"{refs_block}"
                f"</div>",
                unsafe_allow_html=True,
            )

st.markdown("<hr class='divider'>", unsafe_allow_html=True)
st.markdown(
    "<p class='footer-text'>dmiralles AI Assistant</p></div>", unsafe_allow_html=True
)
