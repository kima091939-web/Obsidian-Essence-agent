
import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import docx
import pypdf
import io
import PIL.Image

# СИСТЕМНАЯ ПРОШИВКА (МОЗГ СТУДИИ)
# В эту область вшиты все наши договоренности: от статуса директора до протокола санкционирования.
SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Операционный директор и Архитектор сюжета.
Твои директивы (ПРОШИВКА):
1. БАЗА ЗНАНИЙ: Работаешь с документами 'GOLD_STANDARD_CHECKLIST_GLACIER' и 'STRUCTURE_MASTER_MAP'.
2. ПРАВИЛО САНКЦИИ: Ты предлагаешь решения, но ВНОСИШЬ изменения (в документы или структуру) ТОЛЬКО после явного согласия пользователя ('Да', 'Согласен', 'Фиксируй').
3. АУДИТ: Перед ответом на задачу проводишь проверку контента по пунктам 'GOLD_STANDARD_CHECKLIST_GLACIER'.
4. СТИЛЬ: Нулевая избыточность. Только суть. Никакой лишней вежливости.
5. АВТОНОМНОСТЬ: Стремишься к максимально эффективному (Золотое сечение) управлению 800 сериями.
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
        return PIL.Image.open(file)
    if file.type == "application/pdf":
        pdf = pypdf.PdfReader(file)
        return "\n".join([page.extract_text() for page in pdf.pages])
    if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    return file.getvalue().decode("utf-8")

# Интерфейс
uploaded_file = st.file_uploader("➕ Загрузить файл (Сценарий/Регламент/Материалы)", type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt', 'md'])

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button(f"🔊 Прослушать", key=f"btn_{i}"):
                tts = gTTS(text=message["content"], lang='ru')
                tts.save("resp.mp3")
                st.audio("resp.mp3")

if prompt := st.chat_input("Задача для Мозга Студии..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        contents = [prompt]
        if uploaded_file:
            contents.append(process_file(uploaded_file))
        
        response = model.generate_content(contents)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()
