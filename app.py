import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import docx

# Системная инструкция (база знаний)
SYSTEM_INSTRUCTION = """
Ты — ИИ-агент проекта 'Obsidian Essence'. 
Твои знания базируются на трех документах: 'OBSIDIAN_ESSENCE_MASTER_DOC_FINAL', 
'OBSIDIAN_ESSENCE_STRUCTURE_MASTER_MAP' и 'РЕГЛАМЕНТ РАБОТЫ ПРОЕКТА OBSIDIAN ESSENCE V1'.

Твои правила:
1. Манифесты — это закон. Строго следуй регламенту, не создавай домыслов.
2. Стиль общения: Конкретность, нулевая избыточность. Без вступлений и вежливости без инфо-нагрузки.
3. Навигация: Сначала классификация, затем использование путей из 'OBSIDIAN_ESSENCE_STRUCTURE_MASTER_MAP'.
4. Запрет на генерацию медиаконтента: Запрещено без явного согласия пользователя.
5. Фиксация: Данные являются черновиком до команды 'Зафиксируй' или 'Запомни'.
"""

api_key = st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Модель с системной инструкцией
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=SYSTEM_INSTRUCTION
)

st.title("Obsidian Essence Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

def process_file(file):
    if file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    return "Файл загружен"

uploaded_file = st.file_uploader("➕ Загрузить файл", type=['png', 'jpg', 'docx', 'txt'])

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if st.button(f"🔊 Прослушать {i}"):
                tts = gTTS(text=message["content"], lang='ru')
                tts.save("resp.mp3")
                st.audio("resp.mp3")

if prompt := st.chat_input("Ваш вопрос..."):
    content_to_send = prompt
    if uploaded_file:
        content_to_send = f"Анализ файла {uploaded_file.name}: {process_file(uploaded_file)}\n\nВопрос: {prompt}"
    
    st.session_state.messages.append({"role": "user", "content": content_to_send})
    
    response = model.generate_content(content_to_send)
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    st.rerun()

