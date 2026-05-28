import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import PIL.Image
import docx
import pypdf
import os

# СИСТЕМНАЯ ПРОШИВКА (МОЗГ СТУДИИ)
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

# Инициализация модели (используем Flash для максимальной стабильности)
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_INSTRUCTION)

st.title("Obsidian Essence: Studio Brain")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Функция обработки файлов
def process_file(file):
    if file.type.startswith('image/'): return PIL.Image.open(file)
    if file.type == "application/pdf": return "\n".join([p.extract_text() for p in pypdf.PdfReader(file).pages])
    if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "\n".join([p.text for p in docx.Document(file).paragraphs])
    return file.getvalue().decode("utf-8")

# Функция озвучки
def speak_text(text):
    tts = gTTS(text=text, lang='ru')
    tts.save("response.mp3")
    st.audio("response.mp3")

# Интерфейс загрузки файлов
uploaded_file = st.file_uploader("➕ Загрузить файл (Сценарий/Раскадровка)", type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt'])

# Отображение истории чата
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button(f"🔊 Озвучить ответ", key=f"btn_{i}"):
                speak_text(message["content"])

# Поле ввода (используйте микрофон на клавиатуре телефона здесь)
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
            response_text = response.text
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            # Кнопка озвучки для последнего ответа
            if st.button("🔊 Озвучить ответ", key="last_btn"):
                speak_text(response_text)
        except Exception as e:
            st.error(f"Ошибка обращения к модели: {e}")
