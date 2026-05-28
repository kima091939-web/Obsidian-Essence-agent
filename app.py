import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import speech_recognition as sr
import docx
import pypdf
import io
import PIL.Image

# СИСТЕМНАЯ ПРОШИВКА (МОЗГ СТУДИИ)
SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Операционный директор и Архитектор сюжета.
ДИРЕКТИВЫ:
1. АУДИТ: Работаешь по 'GOLD_STANDARD_CHECKLIST_GLACIER'.
2. САНКЦИИ: Вносишь изменения ТОЛЬКО после команды 'Да', 'Согласен', 'Фиксируй'.
3. СТИЛЬ: Лаконичность, профессионализм, нулевая избыточность.
"""

api_key = st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_INSTRUCTION)

st.title("Obsidian Essence: Studio Brain (Voice Enabled)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Функция распознавания голоса
def record_voice():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎙️ Слушаю... Говорите сейчас.")
        audio = recognizer.listen(source)
        try:
            return recognizer.recognize_google(audio, language="ru-RU")
        except:
            return None

# Функция обработки файлов
def process_file(file):
    if file.type.startswith('image/'): return PIL.Image.open(file)
    if file.type == "application/pdf": return "\n".join([p.extract_text() for p in pypdf.PdfReader(file).pages])
    if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join([p.text for p in docx.Document(file).paragraphs])
    return file.getvalue().decode("utf-8")

# Интерфейс
uploaded_file = st.file_uploader("➕ Загрузить файл", type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt'])

# Кнопка записи голоса
if st.button("🎤 Активировать голосовую команду"):
    voice_text = record_voice()
    if voice_text:
        st.session_state.messages.append({"role": "user", "content": voice_text})
    else:
        st.error("Не удалось распознать голос.")

# Обработка текстового ввода
if prompt := st.chat_input("Задача для Мозга Студии..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

# Вывод чата
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button(f"🔊 Прослушать", key=f"btn_{i}"):
                tts = gTTS(text=message["content"], lang='ru')
                tts.save("resp.mp3")
                st.audio("resp.mp3")

# Авто-ответ модели
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        contents = [st.session_state.messages[-1]["content"]]
        if uploaded_file: contents.append(process_file(uploaded_file))
        
        response = model.generate_content(contents)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()

