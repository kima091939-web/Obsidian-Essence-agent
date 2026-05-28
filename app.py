import streamlit as st
import pyttsx3
import whisper
from drive_manager import DriveManager
from ai_engine import StudioBrain
from audio_recorder_streamlit import audio_recorder

# --- ИНИЦИАЛИЗАЦИЯ (Золотой стандарт) ---
@st.cache_resource
def get_systems():
    drive = DriveManager(st.secrets["gcp_service_account"])
    tools = [drive.list_folder, drive.read_file, drive.update_file]
    brain = StudioBrain(st.secrets["GOOGLE_API_KEY"], tools)
    whisper_model = whisper.load_model("base")
    return drive, brain, whisper_model

drive, brain, whisper_model = get_systems()

if "chat" not in st.session_state:
    st.session_state.chat = brain.get_chat()

st.title("🚀 Obsidian Essence: Ultra-Director")

# --- ЛОГИКА АУДИО (Прокачанная) ---
def speak(text):
    engine = pyttsx3.init()
    engine.save_to_file(text, 'response.mp3')
    engine.runAndWait()
    st.audio("response.mp3")

# --- ИНТЕРФЕЙС ---
audio_bytes = audio_recorder("Нажми для записи команды...")
if audio_bytes:
    with open("audio.wav", "wb") as f: f.write(audio_bytes)
    user_text = whisper_model.transcribe("audio.wav")["text"]
    st.chat_message("user").markdown(user_text)
    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(user_text)
        st.markdown(response.text)
        speak(response.text)

if prompt := st.chat_input("Оперативная команда..."):
    with st.chat_message("user"): st.markdown(prompt)
    with st.chat_message("assistant"):
        response = st.session_state.chat.send_message(prompt)
        st.markdown(response.text)
        speak(response.text)
