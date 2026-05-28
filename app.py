import streamlit as st
from drive_manager import DriveManager
from ai_engine import StudioBrain

st.set_page_config(page_title="Obsidian Essence: Operational Director", layout="wide")

# Инициализация сервисов
if "drive" not in st.session_state:
    st.session_state.drive = DriveManager(st.secrets["gcp_service_account"])
    
tools = [st.session_state.drive.list_folder, st.session_state.drive.read_file, st.session_state.drive.update_file]
brain = StudioBrain(st.secrets["GOOGLE_API_KEY"], tools)

if "chat" not in st.session_state:
    st.session_state.chat = brain.get_chat()

st.title("🧠 Obsidian Essence: Operational Director")

# Чат
for message in st.session_state.chat.history:
    role = "assistant" if message.role == "model" else "user"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

if prompt := st.chat_input("Дай команду..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(prompt)
        st.markdown(response.text)

