import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import PIL.Image
import docx
import pypdf
import os

# СИСТЕМНАЯ ПРОШИВКА
SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Операционный директор и Архитектор сюжета.
ДИРЕКТИВЫ:
1. АУДИТ: Работаешь строго по 'GOLD_STANDARD_CHECKLIST_GLACIER'.
2. САНКЦИИ: Вносишь изменения ТОЛЬКО после команды 'Да', 'Согласен', 'Фиксируй'.
3. СТИЛЬ: Лаконичность, профессионализм, нулевая избыточность.
"""

# Настройка API
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Ошибка: Ключ API не найден в настройках Secrets!")
    st.stop()

# Инициализация модели
model = genai.GenerativeModel(
    model_name='gemini-1.5-pro',
    system_instruction=SYSTEM_INSTRUCTION
)

st.title("Obsidian Essence: Studio Brain")

if "messages" not in st.session_state:
    st.session_state.messages = []

def process_file(file):
    try:
        if file.type.startswith('image/'): return PIL.Image.open(file)
        if file.type == "application/pdf": 
            reader = pypdf.PdfReader(file)
            return "\n".join([page.extract_text() for page in reader.pages])
        if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file)
            return "\n".join([para.text for para in doc.paragraphs])
        return file.getvalue().decode("utf-8")
    except Exception:
        return "Ошибка чтения файла."

def speak_text(text):
    tts = gTTS(text=text, lang='ru')
    tts.save("response.mp3")
    st.audio("response.mp3")

uploaded_file = st.file_uploader("➕ Загрузить файл", type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt'])

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button(f"🔊 Озвучить", key=f"btn_{i}"):
                speak_text(message["content"])

if prompt := st.chat_input("Введите задачу для Мозга Студии..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        contents = [prompt]
        if uploaded_file:
            contents.append(process_file(uploaded_file))
        try:
            response = model.generate_content(contents)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка API: {e}")

