import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder
import os

# Заголовок приложения
st.title("Obsidian Essence Agent")

# Получение ключа из настроек Streamlit (Secrets)
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("API-ключ не найден. Добавьте его в настройки Streamlit.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    # Интерфейс чата
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Отображение истории
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Кнопка озвучки для сообщений ассистента
            if message["role"] == "assistant":
                if st.button(f"🔊 Прослушать ответ {i}"):
                    tts = gTTS(text=message["content"], lang='ru')
                    tts.save("response.mp3")
                    st.audio("response.mp3", format="audio/mp3")

    # Голосовой ввод
    audio = mic_recorder(start_prompt="🎙️ Нажмите, чтобы говорить", stop_prompt="⏹️ Остановить", key='mic')
    
    # Обработка ввода (текст или голос)
    prompt = st.chat_input("Что спросим у Obsidian?")
    
    if audio:
        # Здесь должна быть логика распознавания речи (STT), 
        # пока используем аудио-контейнер для проверки
        st.write("Аудио получено, но требует подключения API для распознавания речи.")
    
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = model.generate_content(prompt)
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()
