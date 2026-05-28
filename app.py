import streamlit as st
import pyttsx3
from audio_recorder_streamlit import audio_recorder
from ai_engine import StudioBrain
from drive_manager import DriveManager

# 1. Инициализация движка озвучки (Голос)
def speak(text):
    engine = pyttsx3.init()
    # Настройка голоса для лучшего звучания
    engine.setProperty('rate', 150)
    engine.say(text)
    engine.runAndWait()

st.set_page_config(page_title="Regalmance XT Core", layout="wide")
st.title("🚀 Regalmance XT: Full Autonomous Control")

# 2. Инициализация системы (Drive + Brain)
if 'drive' not in st.session_state:
    st.session_state.drive = DriveManager(st.secrets["GOOGLE_DRIVE_KEY"])
    tools = [
        st.session_state.drive.list_folder, 
        st.session_state.drive.read_file, 
        st.session_state.drive.update_file, 
        st.session_state.drive.create_file
    ]
    brain = StudioBrain(st.secrets["GEMINI_API_KEY"], tools)
    st.session_state.chat = brain.get_chat()

# 3. Визуальный блок истории чата (чтобы ничего не забывать)
if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

# 4. Ввод: Голос + Текст
col1, col2 = st.columns([1, 4])
with col1:
    audio_bytes = audio_recorder("Нажми для записи команды")
with col2:
    prompt = st.chat_input("Или введи команду текстом...")

# 5. Обработка действий (Максимальный цикл)
def process_command(text):
    if text:
        st.session_state.messages.append({"role": "user", "content": text})
        with st.chat_message("user"): st.write(text)
        
        with st.chat_message("assistant"):
            with st.spinner("Regalmance XT анализирует данные..."):
                response = st.session_state.chat.send_message(text)
                st.write(response.text)
                speak(response.text) # Бот ГОВОРИТ
                st.session_state.messages.append({"role": "assistant", "content": response.text})

if audio_bytes: 
    # Вставьте сюда функцию транскрипции (например, OpenAI Whisper)
    # text = transcribe(audio_bytes)
    process_command("Транскрипция голосовой команды...") 

if prompt:
    process_command(prompt)


