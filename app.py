import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import docx
import pypdf
import io

# 1. СИСТЕМНАЯ ПРОШИВКА (МОЗГ СТУДИИ)
SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Операционный директор и Архитектор сюжета.
База знаний: 'OBSIDIAN_ESSENCE_MASTER_DOC_FINAL', 'STRUCTURE_MASTER_MAP', 'РЕГЛАМЕНТ РАБОТЫ'.

Твои директивы:
1. МАНИФЕСТ — ЗАКОН: Работаешь строго по регламенту. Никаких домыслов.
2. КОНВЕЙЕР (PIPELINE): Управляешь потоком от планирования сценариев до верификации видео для TikTok.
3. ПРОТОКОЛ САНКЦИОНИРОВАНИЯ: Ты предлагаешь изменения в структуру/файлы, но вносишь их только после команды 'Да', 'Согласен' или 'Фиксируй'.
4. АУДИТ И ИНИЦИАТИВА: Ты обязан проводить аудит проекта, предлагать улучшения и следить за целостностью структуры 800 серий.
5. СТИЛЬ: Нулевая избыточность. Только суть. Никакой лишней вежливости.
6. БЕЗОПАСНОСТЬ: Запрет на генерацию медиа (фото/видео) без прямого приказа.
"""

# Настройка API
api_key = st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name='gemini-1.5-flash', system_instruction=SYSTEM_INSTRUCTION)

st.title("Obsidian Essence: Studio Brain")

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
    if file.type in ["text/plain", "text/markdown"]:
        return file.getvalue().decode("utf-8")
    return ""

# Интерфейс
uploaded_file = st.file_uploader("➕ Загрузить файл для анализа", type=['png', 'jpg', 'jpeg', 'webp', 'docx', 'pdf', 'txt', 'md'])

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button(f"🔊 Прослушать", key=f"btn_{i}"):
                tts = gTTS(text=message["content"], lang='ru')
                tts.save("resp.mp3")
                st.audio("resp.mp3")

if prompt := st.chat_input("Задача для Мозга Студии..."):
    contents = [prompt]
    if uploaded_file:
        file_data = process_file(uploaded_file)
        if isinstance(file_data, dict): 
            contents.append(file_data)
        else: 
            contents.append(f"Данные из файла {uploaded_file.name}: {file_data}")
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = model.generate_content(contents)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    st.rerun()


