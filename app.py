import json
import streamlit as st
import pyttsx3
from ai_engine import StudioBrain
from drive_manager import DriveManager

def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()

st.set_page_config(page_title="Regalmance XT Core", layout="wide")
st.title("🚀 Regalmance XT: Full Autonomous Control (v3.5)")

if 'smart_search' not in st.session_state: st.session_state.smart_search = False
if 'web_access' not in st.session_state: st.session_state.web_access = False

st.sidebar.title("🛠 Контроль системы")
st.session_state.smart_search = st.sidebar.toggle("🔐 Интеллектуальный поиск", value=st.session_state.smart_search)
st.session_state.web_access = st.sidebar.toggle("🌐 Доступ в Интернет", value=st.session_state.web_access)
st.sidebar.divider()

if 'brain' not in st.session_state:
    creds_info = json.loads(st.secrets["GOOGLE_DRIVE_KEY"])
    drive = DriveManager(creds_info)
    st.session_state.brain = StudioBrain(st.secrets["GEMINI_API_KEY"], drive)

if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

if prompt := st.chat_input("Введите команду..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Regalmance XT (3.5) думает..."):
            chat = st.session_state.brain.get_chat(st.session_state.smart_search, st.session_state.web_access)
            response = chat.send_message(prompt)
            st.write(response.text)
            speak(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
