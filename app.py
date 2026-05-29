import json
import io
import streamlit as st
from gtts import gTTS
from ai_engine import StudioBrain
from drive_manager import DriveManager

def speak(text: str):
    try:
        tts = gTTS(text=text, lang="ru")
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        st.audio(buf, format="audio/mp3")
    except Exception as e:
        st.warning(f"Ошибка озвучки: {e}")

st.set_page_config(page_title="Regalmance XT Core", layout="wide")
st.title("🚀 Regalmance XT: Full Autonomous Control (v3.5)")

st.sidebar.title("🛠 Контроль системы")

if "file_access" not in st.session_state:
    st.session_state.file_access = False
if "web_access" not in st.session_state:
    st.session_state.web_access = False
if "write_mode" not in st.session_state:
    st.session_state.write_mode = False
if "audit_mode" not in st.session_state:
    st.session_state.audit_mode = False

st.session_state.file_access = st.sidebar.toggle(
    "📁 Доступ к файлам", value=st.session_state.file_access
)
st.session_state.web_access = st.sidebar.toggle(
    "🌐 Доступ в интернет", value=st.session_state.web_access
)
st.session_state.write_mode = st.sidebar.toggle(
    "✏️ Режим записи", value=st.session_state.write_mode
)
st.session_state.audit_mode = st.sidebar.toggle(
    "🔍 Аудит проекта", value=st.session_state.audit_mode
)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"📁 Файлы: {'✅' if st.session_state.file_access else '❌'}  \n"
    f"🌐 Интернет: {'✅' if st.session_state.web_access else '❌'}  \n"
    f"✏️ Запись: {'✅' if st.session_state.write_mode else '❌'}  \n"
    f"🔍 Аудит: {'✅' if st.session_state.audit_mode else '❌'}"
)

if "brain" not in st.session_state:
    try:
        creds_info = json.loads(st.secrets["GOOGLE_DRIVE_KEY"])
        drive = DriveManager(creds_info)
        st.session_state.brain = StudioBrain(st.secrets["GEMINI_API_KEY"], drive)
        st.sidebar.success("Движок инициализирован ✅")
    except Exception as e:
        st.sidebar.error(f"Ошибка инициализации: {e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

input_text = st.chat_input("Введите или скажите команду 🎤")

if input_text:
    st.session_state.messages.append({"role": "user", "content": input_text})
    with st.chat_message("user"):
        st.write(input_text)

    with st.chat_message("assistant"):
        with st.spinner("Regalmance XT думает..."):
            try:
                chat = st.session_state.brain.get_chat(
                    file_access=st.session_state.file_access,
                    web_access=st.session_state.web_access,
                    write_mode=st.session_state.write_mode,
                    audit_mode=st.session_state.audit_mode,
                )
                response = chat.send_message(input_text)
                answer = response.text
                st.write(answer)
                speak(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Ошибка ответа: {e}")
