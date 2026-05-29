import json
import streamlit as st
import pyttsx3
from ai_engine import StudioBrain
from drive_manager import DriveManager

# 1. Инициализация движка озвучки (Голос)
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()

st.set_page_config(page_title="Regalmance XT Core", layout="wide")
st.title("🚀 Regalmance XT: Full Autonomous Control")

# --- ПАНЕЛЬ УПРАВЛЕНИЯ РЕЖИМАМИ ---
if 'smart_search' not in st.session_state: st.session_state.smart_search = False
if 'web_access' not in st.session_state: st.session_state.web_access = False

st.sidebar.title("🛠 Контроль системы")
st.session_state.smart_search = st.sidebar.toggle("🔐 Интеллектуальный поиск", value=st.session_state.smart_search)
st.session_state.web_access = st.sidebar.toggle("🌐 Доступ в Интернет", value=st.session_state.web_access)
st.sidebar.divider()
# ----------------------------------

# 2. Инициализация системы (Drive + Brain)
if 'drive' not in st.session_state:
    creds_info = json.loads(st.secrets["GOOGLE_DRIVE_KEY"])
    st.session_state.drive = DriveManager(creds_info)
    
    tools = [
        st.session_state.drive.list_folder, 
        st.session_state.drive.read_file, 
        st.session_state.drive.update_file, 
        st.session_state.drive.create_file
    ]
    brain = StudioBrain(st.secrets["GEMINI_API_KEY"], tools)
    st.session_state.chat = brain.get_chat()

# 3. Визуальный блок истории чата
if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

# 4. Ввод: Только Текст
prompt = st.chat_input("Введите команду для Regalmance XT...")

# 5. Обработка действий
def process_command(text):
    if text:
        st.session_state.messages.append({"role": "user", "content": text})
        with st.chat_message("user"): st.write(text)
        
        with st.chat_message("assistant"):
            with st.spinner("Regalmance XT думает..."):
                # Сюда позже мы добавим логику передачи флагов smart_search и web_access в промпт
                response = st.session_state.chat.send_message(text)
                st.write(response.text)
                speak(response.text) # Бот ГОВОРИТ через динамики
                st.session_state.messages.append({"role": "assistant", "content": response.text})

if prompt:
    process_command(prompt)

