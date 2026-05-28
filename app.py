import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
import io

# Заголовок приложения
st.title("Obsidian Essence Agent")

# Конфигурация API
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("API-ключ не найден. Добавьте его в настройки Streamlit.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    # Инициализация истории чата
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Функция распознавания речи
    def speech_to_text(audio_bytes):
        recognizer = sr.Recognizer()
        audio_file = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_content = recognizer.record(source)
        return recognizer.recognize_google(audio_content, language="ru-RU")

    # Отображение истории чата
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                if st.button(f"🔊 Прослушать {i}"):
                    tts = gTTS(text=message["content"], lang='ru')
                    tts.save("response.mp3")
                    st.audio("response.mp3", format="audio/mp3")

    # Голосовой ввод
    audio_data = mic_recorder(start_prompt="🎙️ Нажать для записи", stop_prompt="⏹️ Остановить", key='mic')
    
    if audio_data:
        try:
            text = speech_to_text(audio_data['bytes'])
            st.session_state.messages.append({"role": "user", "content": text})
            st.rerun()
        except Exception as e:
            st.error("Не удалось распознать речь.")

    # Текстовый ввод
    if prompt := st.chat_input("Что спросим у Obsidian?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # Генерация ответа, если последнее сообщение от пользователя
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        user_text = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            response = model.generate_content(user_text)
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()
