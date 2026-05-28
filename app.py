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
# Убедитесь, что в Streamlit Secrets ключ называется именно GOOGLE_API_KEY
api_key = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)

# Инициализация модели БЕЗ указания версии (использует стабильный путь по умолчанию)
model = genai.GenerativeModel('gemini-1.5-pro')

st.title("Obsidian Essence: Studio Brain")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Функция обработки файлов
def process_file(file):
    try:
        if file.type.startswith('image/'): return PIL.Image.open(file)
        if file.type == "application/pdf": 
            return "\n".join([page.extract_text() for page in pypdf.PdfReader(file).pages])
        if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([para.text for para in docx.Document(file).paragraphs])
        return file.getvalue().decode("utf-8")
    except Exception:
        return "Ошибка чтения файла."

# Функция озвучки
def speak_text(text):
    tts = gTTS(text=text, lang='ru')
    tts.save("response.mp3")
    st.audio("response.mp3")

# Интерфейс
uploaded_file = st.file_uploader("➕ Загрузить файл", type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt'])

# Отображение чата
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button(f"🔊 Озвучить", key=f"btn_{i}"):
                speak_text(message["content"])

# Ввод задачи
if prompt := st.chat_input("Введите задачу для Мозга Студии..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        contents = [prompt]
        if uploaded_file:
            contents.append(process_file(uploaded_file))
        
        try:
            # Генерация ответа через модель
            response = model.generate_content(contents)
            response_text = response.text
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            # Перезагрузка для отображения кнопки озвучки
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка API: {e}")
