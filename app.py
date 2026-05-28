import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import docx
import pypdf
import io

# 1. СИСТЕМНАЯ ПРОШИВКА (База знаний проекта)
SYSTEM_INSTRUCTION = """
Ты — ИИ-агент проекта 'Obsidian Essence'. 
Твои знания базируются на документах: 'OBSIDIAN_ESSENCE_MASTER_DOC_FINAL', 
'OBSIDIAN_ESSENCE_STRUCTURE_MASTER_MAP' и 'РЕГЛАМЕНТ РАБОТЫ ПРОЕКТА OBSIDIAN ESSENCE V1'.

Твои директивы:
1. Манифесты — закон. Работай строго по регламенту, никаких домыслов.
2. Стиль: Конкретность, нулевая избыточность. Без лишних слов.
3. Навигация: Используй пути из 'OBSIDIAN_ESSENCE_STRUCTURE_MASTER_MAP'.
4. Запрет медиагенерации: Не создавай изображения/видео без явной команды.
5. Фиксация: Данные — 'черновик', пока не дана команда 'Зафиксируй' или 'Запомни'.
"""

# Настройка API
api_key = st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_INSTRUCTION)

st.title("Obsidian Essence Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Функция обработки файлов
def process_file(file):
    if file.type.startswith('image/'):
        return {"mime_type": file.type, "data": file.getvalue()}
    
    if file.type == "application/pdf":
        pdf = pypdf.PdfReader(file)
        return "\n".join([page.extract_text() for page in pdf.pages])
    
    if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    
    if file.type == "text/plain" or file.type == "text/markdown":
        return file.getvalue().decode("utf-8")
    
    return ""

# Интерфейс
uploaded_file = st.file_uploader("➕ Загрузить файл", type=['png', 'jpg', 'jpeg', 'webp', 'docx', 'pdf', 'txt', 'md'])

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button(f"🔊 Прослушать {i}", key=f"btn_{i}"):
                tts = gTTS(text=message["content"], lang='ru')
                tts.save("resp.mp3")
                st.audio("resp.mp3")

if prompt := st.chat_input("Ваш вопрос..."):
    # Подготовка данных для модели
    contents = [prompt]
    if uploaded_file:
        file_data = process_file(uploaded_file)
        if isinstance(file_data, dict): # Изображение
            contents.append(file_data)
        else: # Текст
            contents.append(f"Анализ файла {uploaded_file.name}: {file_data}")
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Генерация
    response = model.generate_content(contents)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    st.rerun()

