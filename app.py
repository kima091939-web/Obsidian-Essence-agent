import json
import streamlit as st
import pyttsx3
from ai_engine import StudioBrain
from drive_manager import DriveManager

# Инициализация голоса
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()

st.set_page_config(page_title="Regalmance XT Core", layout="wide")
st.title("🚀 Regalmance XT: Full Autonomous Control")

# Инициализация состояний в Session State
if 'smart_search' not in st.session_state: st.session_state.smart_search = False
if 'web_access' not in st.session_state: st.session_state.web_access = False

# Боковая панель управления
st.sidebar.title("🛠 Контроль системы")
st.session_state.smart_search = st.sidebar.toggle("🔐 Интеллектуальный поиск", value=st.session_state.smart_search)
st.session_state.web_access = st.sidebar.toggle("🌐 Доступ в Интернет", value=st.session_state.web_access)
st.sidebar.divider()

# Инициализация ядра системы
if 'brain' not in st.session_state:
    try:
        creds_info = json.loads(st.secrets["GOOGLE_DRIVE_KEY"])
        drive = DriveManager(creds_info)
        st.session_state.brain = StudioBrain(st.secrets["GEMINI_API_KEY"], drive)
    except Exception as e:
        st.error(f"Критическая ошибка инициализации: {e}")
        st.stop()

if "messages" not in st.session_state: st.session_state.messages = []

# Отрисовка истории чата
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

# Обработка пользовательского ввода
if prompt := st.chat_input("Введите команду для Regalmance XT..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Regalmance XT обрабатывает запрос..."):
            try:
                # Получаем чат с текущими флагами
                chat_session = st.session_state.brain.get_chat(st.session_state.smart_search, st.session_state.web_access)
                response = chat_session.send_message(prompt)
                
                st.write(response.text)
                speak(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Ошибка выполнения: {e}")



