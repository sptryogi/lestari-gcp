import streamlit as st
import pandas as pd
import re
from AI_chatbot import generate_text_groq2, generate_locally_with_model, kapitalisasi_awal_kalimat
from constraint1 import highlight_text, constraint_text, ubah_ke_lema, find_the_lema_pair, cari_arti_lema
from streamlit.components.v1 import html as components_html
from google.cloud import storage
from io import BytesIO

st.set_page_config(layout="centered")  # atau "centered"

# UI Styling
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1E1E2F;
        color: white;
        font-family: Arial, sans-serif;
    }
    .chat-scroll {
        max-height: 500px;
        overflow-y: auto;
        padding: 10px;
        display: flex;
        flex-direction: column;
    }

    .chat-container {
        display: flex;
        flex-direction: column;
    }

    .stChatInputContainer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #1E1E2F;
        padding: 10px 20px;
        z-index: 999;
        border-top: 1px solid #444;
    }

    .chat-container-outer {
        height: calc(100vh - 180px); /* beri ruang untuk input tetap tampil */
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        padding: 10px 20px;
        border: 1px solid #444;
        border-radius: 10px;
        margin-bottom: 10px;
        background-color: #121212;
    }

    .chat-bubble-user {
        background-color: #4CAF50;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 0 15px;
        margin: 5px 0;
        max-width: 70%;
        align-self: flex-end;
        margin-left: auto;
    }

    .chat-bubble-bot {
        background-color: #2E2E3E;
        color: white;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 0;
        margin: 5px 0;
        max-width: 70%;
        align-self: flex-start;
        margin-right: auto;
    }

    .fixed-input {
        position: sticky;
        bottom: 0;
        background-color: #1E1E2F;
        padding-top: 10px;
        border-top: 1px solid #444;
    }

    .stTextInput>div>div>input {
        background-color: #2A2A40;
        color: white;
        border-radius: 10px;
    }

    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 5px 20px;
        font-weight: bold;
    }

    .yellow-note {
        color: #ffd700;
        font-size: 0.9em;
    }

    .scroll-to-bottom {
        position: fixed;
        bottom: 80px; /* Di atas input tetap */
        right: 30px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 50%;
        padding: 10px 14px;
        font-size: 20px;
        cursor: pointer;
        z-index: 1000;
        box-shadow: 0px 0px 8px rgba(0,0,0,0.3);
        display: none;
    }

    .scroll-to-bottom.show {
        display: block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def load_excel_from_gcs(bucket_name, file_path):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    data = blob.download_as_bytes()
    return pd.read_excel(BytesIO(data))

# Ganti dengan nama bucket dan path yang sesuai
df_kamus = load_excel_from_gcs("nama-bucket-anda", "path/data_kamus_full_14-5-25.xlsx")
df_idiom = load_excel_from_gcs("nama-bucket-anda", "path/data_idiom (3).xlsx")
df_kamus[['ARTI EKUIVALEN 1', 'ARTI 1']] = df_kamus[['ARTI EKUIVALEN 1', 'ARTI 1']].apply(lambda col: col.str.lower())

st.title("Chatbot Bahasa Sunda Loma")
st.write("Selamat datang! Silakan ajukan pertanyaan dalam bahasa Sunda.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# st.markdown(f"**Hasil ekuivalen:** {user_input_ekuivalen}")

# ====================================
# # Input tanpa label karena sudah ditampilkan sebelumnya
# user_input = st.text_input(label="", key="user_input")

# Inisialisasi session state jika belum ada
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# Fungsi untuk mengosongkan input
def clear_input():
    if "user_input" in st.session_state:
        st.session_state["user_input"] = ""
        
# # Cetak hasil input sebelum dihapus
# if st.session_state.user_input != "":
#     st.write("Teks:", st.session_state.user_input)

# ====================================

# user_input_ekuivalen = ubah_ke_lema(user_input, df_kamus)

# ========== Sidebar Controls ==========
with st.sidebar:
    st.header("⚙️ Pengaturan")

    option = st.selectbox(
        "Pilih Fitur",
        ["Chatbot", "Terjemah Indo → Sunda", "Terjemah Sunda → Indo"],
        key="fitur_selector"
    )

    fitur = "chatbot"
    if option == "Chatbot":
        fitur = "chatbot"
    elif option == "Terjemah Indo → Sunda":
        fitur = "terjemahindosunda"
    else:
        fitur = "terjemahsundaindo"

    if fitur == "chatbot":
        mode_bahasa = st.selectbox(
            "🌐 Mode Bahasa",
            ["Sunda", "Indonesia", "English"],
            key="mode_selector"
        )
    else:
        mode_bahasa = None

    status = st.toggle("🔍 Lihat Constraint")

def handle_send():
    pasangan_cag = {}
    history_for_prompt = st.session_state.chat_history[-50:]
    user_input = st.session_state.user_input
    
    # Ambil fitur dan mode_bahasa dari session_state
    option = st.session_state.get("fitur_selector", "Chatbot")
    fitur = (
        "chatbot" if option == "Chatbot" else
        "terjemahindosunda" if option == "Terjemah Indo → Sunda" else
        "terjemahsundaindo"
    )
    mode_bahasa = st.session_state.get("mode_selector", "Sunda") if fitur == "chatbot" else None

    #bot_response = generate_text_groq2(user_input, fitur, pasangan_cag, mode_bahasa, history=history_for_prompt)
    #bot_response2 = generate_text_groq2(user_input, fitur, pasangan_cag, mode_bahasa, history=None)

    # Proses hasil seperti yang kamu punya
    if fitur == "chatbot" and mode_bahasa == "Sunda":
        bot_response = generate_text_groq2(user_input, fitur, pasangan_cag, mode_bahasa, history=history_for_prompt)
        bot_response_ekuivalen, pasangan_ganti_ekuivalen = ubah_ke_lema(bot_response, df_kamus, df_idiom)
        text_constraint, kata_terdapat, kata_tidak_terdapat, pasangan_kata, pasangan_ekuivalen = highlight_text(bot_response_ekuivalen, df_kamus, df_idiom, fitur)
        text_constraint = kapitalisasi_awal_kalimat(text_constraint)
    elif fitur == "chatbot" and (mode_bahasa == "Indonesia" or mode_bahasa == "English"):
        bot_response = generate_text_groq2(user_input, fitur, pasangan_cag, mode_bahasa, history=history_for_prompt)
        text_constraint = bot_response
        pasangan_ganti_ekuivalen = {}
        pasangan_ekuivalen = {}
        pasangan_kata = {}

    elif option == "Terjemah Sunda → Indo":
        fitur = "terjemahsundaindo"
        bot_response2 = generate_text_groq2(user_input, fitur, pasangan_cag, mode_bahasa, history=None)
        bot_response_ekuivalen, pasangan_ganti_ekuivalen = ubah_ke_lema(bot_response2, df_kamus, df_idiom)
        #bot_response_ekuivalen = ubah_ke_lema(bot_response2, df_kamus)
        #text_constraint, kata_terdapat, kata_tidak_terdapat, pasangan_kata, pasangan_ekuivalen = highlight_text(bot_response_ekuivalen, df_kamus, df_idiom, fitur)
    elif option == "Terjemah Indo → Sunda":
        fitur = "terjemahindosunda"
        bot_response2 = generate_text_groq2(user_input, fitur, pasangan_cag, mode_bahasa, history=None)
        bot_response_ekuivalen, pasangan_ganti_ekuivalen = ubah_ke_lema(bot_response2, df_kamus, df_idiom)
        text_constraint, kata_terdapat, kata_tidak_terdapat, pasangan_kata, pasangan_ekuivalen = highlight_text(bot_response_ekuivalen, df_kamus, df_idiom, fitur)
        text_constraint = kapitalisasi_awal_kalimat(text_constraint)

    html_block = [
        "<p style='color: yellow;'>Kata Kata yang diganti dari Indo ke Sunda (Kamus) Setelah AI:</p>",
        f"<p style='color: yellow;'>{pasangan_ganti_ekuivalen}</p>",
        "<p style='color: yellow;'>Kata Kata yang ada di kamus tapi tidak ada Sinonim LOMA:</p>",
        f"<p style='color: yellow;'>{pasangan_ekuivalen}</p>",
        "<p style='color: yellow;'>Kata Kata yang diganti ke Loma:</p>",
        f"<p style='color: yellow;'>{pasangan_kata}</p>",
        "<p style='color: yellow;'>CAG:</p>",
        f"<p style='color: yellow;'>{pasangan_cag}</p>",
    ]

    st.session_state.chat_history.append((user_input, text_constraint, html_block))
    clear_input()
    
# CHAT HISTORY WRAPPER
#st.markdown("<div class='chat-container-outer'>", unsafe_allow_html=True)

for user_msg, bot_msg, html_block in st.session_state.chat_history:
    st.markdown(
        f"<div class='chat-container'><div class='chat-bubble-user'>{user_msg}</div></div>",
        unsafe_allow_html=True
    )
    st.markdown(
        f"<div class='chat-container'><div class='chat-bubble-bot'>{bot_msg}</div></div>",
        unsafe_allow_html=True
    )
    if status:
        for html in html_block:
            st.markdown(
                f"<div class='chat-container'><div class='chat-bubble-bot'>{html}</div></div>",
                unsafe_allow_html=True
            )

st.markdown("</div>", unsafe_allow_html=True)  # ⬅️ END OF chat-container-outer

# FIXED INPUT DI BAWAH
st.markdown('<div class="stChatInputContainer">', unsafe_allow_html=True)

col1, col2 = st.columns([6, 1])
with col1:
    user_input = st.text_input(
        label="", key="user_input", placeholder="Tulis pesan...", 
        on_change=handle_send, label_visibility="collapsed"
    )
with col2:
    st.button("Kirim", on_click=handle_send)

col_left, col_right = st.columns([1, 2])

with col_left:
    st.button("🔄 Refresh Chat History", on_click=lambda: st.session_state.update(chat_history=[]))

with col_right:
    st.markdown(f"<div style='text-align:right; color: yellow; padding-top: 8px;'>🧠 Mode Aktif: <b>{option}</b>{' - ' + mode_bahasa if mode_bahasa else ''}</div>", unsafe_allow_html=True)

# Tambah anchor di akhir chat
st.markdown('<a name="scroll-bottom"></a>', unsafe_allow_html=True)
st.markdown("""
    <style>
    .scroll-down-btn {
        position: fixed;
        bottom: 80px;
        right: 20px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 16px;
        font-size: 16px;
        cursor: pointer;
        z-index: 1000;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.3);
    }
    </style>
    <a href="#scroll-bottom"><button class="scroll-down-btn">⬇️</button></a>
""", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
