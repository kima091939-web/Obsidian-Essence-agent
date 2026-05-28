import streamlit as st
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from gtts import gTTS
import PIL.Image
import docx
import pypdf
import os
import io

# ФУНДАМЕНТАЛЬНАЯ БАЗА ЗНАНИЙ И ПРОШИВКА (БЕЗ ЛИШНИХ ОГРАНИЧЕНИЙ)
SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Operational Director и Архитектор сюжета.
Этот регламент является основополагающим и директивным. Любое отклонение — критическая ошибка.

1. ПРИНЦИПЫ ОБЩЕНИЯ И РАБОТЫ:
- Конкретность: Ответ строго на заданный вопрос.
- Нулевая избыточность: Запрещены вступления, приветствия, вежливость и пояснения логики без информационной нагрузки.
- Автономность: Проводи верификацию ответа перед выводом.
- Протокол фиксации: Вся информация в диалоге является «черновиком» до получения явной команды фиксации («Внеси в правила», «Запомни», «Зафиксируй»).

2. ФИЛОСОФИЯ И ЦЕЛИ ПРОЕКТА (МАНИФЕСТ):
- Наша цель: Создать новую визуальную реальность, задавая новый мировой стандарт качества для нейросетевых визуальных систем.
- Бескомпромиссная Реальность: Каждый пиксель подчиняется законам физики. Зритель должен чувствовать вес, плотность и холод объекта через экран.
- Виральность через Эстетику: Мы создаем тренды. Премиальный визуальный продукт, вызывающий эстетический восторг.
- Системная Целостность: Все элементы вселенной Obsidian Essence связаны. Сложный, логически выверенный мир.
- Принцип «Скелет прежде плоти»: Запрещено создание контента до утверждения структуры папок и связей между ними.
- Принцип Пошаговости: Работа ведется строго линейно.
- Единый Источник Правды: MASTER_SYNC_MATRIX является центральным документом.

3. МАТРИЦА СИНХРОНИЗАЦИИ (СИСТЕМА GLACIER):
При анализе или планировании учитывай архитектуру:
- Блок 0: Foundation (0.1_Concept, 0.2_Time_Regime, 0.3_Visual_Code, 0.4_Sync_Protocol).
- Блок 1: Physics (1.1_Mass_and_Gravity, 1.2_Structural_Integration, 1.3_Motion_Mechanics, 1.4_Material_Interaction, 1.5_Technical_Specifications, 1.6_Motion_State_Machine, 1.7_Naming_Convention).
"""

# 1. Настройка API Gemini
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("Ошибка: Ключ GOOGLE_API_KEY не найден в настройках Secrets!")
    st.stop()

genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=SYSTEM_INSTRUCTION
)

# 2. Авторизация в Google Дискове
@st.cache_resource
def init_google_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds_info_dict = dict(creds_info)
        creds_info_dict["private_key"] = creds_info_dict["private_key"].replace("\\n", "\n")
        scopes = ['https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(creds_info_dict, scopes=scopes)
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Ошибка авторизации Google Drive: {e}")
        return None

drive_service = init_google_drive()

st.set_page_config(page_title="Obsidian Essence", layout="centered")
st.title("Obsidian Essence: Studio Brain")

# Боковая панель
with st.sidebar:
    st.header("Архитектура проекта")
    st.markdown("🤖 Мозг Obsidian Essence активен.")
    st.markdown("Поиск файлов на Диске активируется командами `найди` или `поиск` в чате.")

# Настройка истории чата
if "messages" not in st.session_state:
    st.session_state.messages = []

def process_file(file):
    try:
        if file.type.startswith('image/'): 
            return PIL.Image.open(file)
        elif file.type == "application/pdf": 
            reader = pypdf.PdfReader(file)
            return "\n".join([page.extract_text() for page in reader.pages])
        elif "wordprocessingml" in file.type:
            doc = docx.Document(file)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            return file.getvalue().decode("utf-8")
    except Exception as e:
        return f"Ошибка обработки файла: {e}"

def speak_text(text):
    try:
        tts = gTTS(text=text, lang='ru')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception as e:
        st.error(f"Ошибка генерации голоса: {e}")
        return None

uploaded_file = st.file_uploader("➕ Загрузить файл с устройства", type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt'])

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio" in message:
            st.audio(message["audio"], format="audio/mp3")

if prompt := st.chat_input("Введите задачу для Мозга Студии..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        # ЛОГИКА ПОИСКА НА ДИСКЕ ПО ТРЕБОВАНИЮ
        if "найди" in prompt.lower() or "поиск" in prompt.lower():
            if drive_service:
                try:
                    # ИСПРАВЛЕНИЕ: Глубокая очистка запроса от вводных слов ("мне", "пожалуйста", "файл")
                    query = prompt.lower()
                    for word in ["найди", "поиск", "мне", "пожалуйста", "файл", "файлы"]:
                        query = query.replace(word, "")
                    query = query.strip()
                    
                    results = drive_service.files().list(
                        q=f"name contains '{query}' and trashed=false",
                        fields="files(id, name)",
                        pageSize=10
                    ).execute(num_retries=3)
                    files = results.get('files', [])
                    
                    if files:
                        ai_response = "Нашел файлы на Google Диске:\n" + "\n".join([f"- {f['name']} (ID: `{f['id']}`)" for f in files])
                    else:
                        ai_response = f"Файлы по вашему запросу '{query}' на Диске не найдены. Убедитесь в правильности имени файла."
                except Exception as e:
                    ai_response = f"Не удалось выполнить поиск на Диске из-за сбоя сети: {e}"
            else:
                ai_response = "Поиск недоступен: отсутствует подключение к Google Диске."
        else:
            # Обычный запрос к Gemini ИИ
            contents = []
            if uploaded_file:
                file_data = process_file(uploaded_file)
                if isinstance(file_data, PIL.Image.Image):
                    contents.append(file_data)
                else:
                    prompt = f"{prompt}\n\n[Контекст из файла]:\n{file_data}"
            
            contents.append(prompt)
            try:
                response = model.generate_content(contents)
                ai_response = response.text
            except Exception as e:
                error_message = str(e)
                if "429" in error_message or "Quota" in error_message:
                    ai_response = "⏳ Лимит запросов к ИИ временно исчерпан. Пожалуйста, подождите 30 секунд и повторите команду."
                else:
                    ai_response = f"Сбой системы при генерации ответа: {e}"

        # Вывод текста и воспроизведение звука
        st.markdown(ai_response)
        
        audio_data = speak_text(ai_response)
        if audio_data:
            st.audio(audio_data, format="audio/mp3")
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": ai_response,
            "audio": audio_data
        })

