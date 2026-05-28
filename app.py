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
api_key = st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# ИСПОЛЬЗУЕМ ВЕРСИЮ PRO
model = genai.GenerativeModel(model_name='gemini-1.5-pro', system_instruction=SYSTEM_INSTRUCTION)

st.title("Obsidian Essence: Studio Brain (Pro Mode)")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Функция обработки файлов
def process_file(file):
    try:
        if file.type.startswith('image/'): return PIL.Image.open(file)
        if file.type == "application/pdf": return "\n".join([p.extract_text() for p in pypdf.PdfReader(file).pages])
        if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return "\n".join([p.text for p in docx.Document(file).paragraphs])
        return file.getvalue().decode("utf-8")
    except Exception as e:
        return f"Ошибка чтения файла: {e}"

# Функция озвучки
def speak_text(text):
    tts = gTTS(text=text, lang='ru')
    tts.save("resp.mp3")
    st.audio("resp.mp3")

# Интерфейс
uploaded_file = st.file_uploader("➕ Загрузить файл", type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt'])

# Отображение чата
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button(f"🔊 Озвучить", key=f"btn_{i}"):
                speak_text(message["content"])

# Ввод
if prompt := st.chat_input("Введите задачу..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# Ответ модели
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with st.chat_message("assistant"):
        contents = [st.session_state.messages[-1]["content"]]
        if uploaded_file: contents.append(process_file(uploaded_file))
        
        try:
            response = model.generate_content(contents)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            st.rerun()
        except Exception as e:
            st.error(f"Ошибка модели: {e}")
