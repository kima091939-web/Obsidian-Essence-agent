import streamlit as st
from audio_recorder_streamlit import audio_recorder
import pyttsx3
from ai_engine import StudioBrain
from drive_manager import DriveManager

# Инициализация движка озвучки (локально)
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

st.title("Obsidian Essence: Autonomous Command Center")

# Инициализация менеджеров (через st.session_state для сохранения контекста)
if 'drive' not in st.session_state:
    st.session_state.drive = DriveManager(st.secrets["GOOGLE_DRIVE_KEY"])
if 'chat' not in st.session_state:
    brain = StudioBrain(st.secrets["GEMINI_API_KEY"], 
                        [st.session_state.drive.list_folder, 
                         st.session_state.drive.read_file, 
                         st.session_state.drive.update_file, 
                         st.session_state.drive.create_file])
    st.session_state.chat = brain.get_chat()

# Голосовой ввод
audio_bytes = audio_recorder("Нажмите для голосовой команды")
if audio_bytes:
    # Здесь добавляется логика транскрипции (например, через OpenAI Whisper)
    # user_text = transcribe(audio_bytes) 
    st.write("Команда принята: ", user_text)
    response = st.session_state.chat.send_message(user_text)
    st.write(response.text)
    speak(response.text) # Озвучка ответа агента

