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
import re

# ФУНДАМЕНТАЛЬНАЯ БАЗА ЗНАНИЙ И ПРОШИВКА
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
При анализ или планировании учитывай архитектуру:
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

with st.sidebar:
    st.header("Архитектура проекта")
    st.markdown("🤖 Мозг Obsidian Essence активен.")
    st.markdown("Поиск файлов на Диске активируется командами `найди` или `поиск` в чате.")

if "messages" not in st.session_state:
    st.session_state.messages = []

def process_file(file):
    try:
        if file.type.startswith('image/'): 
            return PIL.Image.open(file)
        elif file.type == "application/pdf": 
            reader = pypdf.PdfReader(file)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif "wordprocessingml" in file.type:
            doc = docx.Document(file)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            return file.getvalue().decode("utf-8")
    except Exception as e:
        return f"Ошибка обработки файла: {e}"

def speak_text(text):
    try:
        # Очистка текста от Markdown разметки для корректного чтения
        clean_text = re.sub(r'[*_`#\-]', '', text)
        if len(clean_text) > 300:  # Ограничение длины озвучки во избежание зависаний
            clean_text = clean_text[:300] + "... Текст сокращен для аудио."
            
        tts = gTTS(text=clean_text, lang='ru')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()  # Возвращаем байты вместо живого потока
    except Exception as e:
        st.error(f"Ошибка генерации голоса: {e}")
        return None

# Генерация уникального ключа для виджета, чтобы сбрасывать его при необходимости
if "file_uploader_key" not in st.session_state:
    st.session_state.file_uploader_key = "file_uploader_0"

uploaded_file = st.file_uploader(
    "➕ Загрузить файл с устройства", 
    type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt'],
    key=st.session_state.file_uploader_key
)

# Отрисовка истории чата
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("audio"):
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
                    query_clean = prompt
                    for word in ["Найди", "найди", "Поиск", "поиск", "мне", "Мне", "пожалуйста", "Пожалуйста", "файл", "файлы"]:
                        query_clean = query_clean.replace(word, "")
                    query_clean = query_clean.strip()
                    
                    q_query = f"(name contains '{query_clean}' or name contains '{query_clean.lower()}') and trashed=false"
                    
                    results = drive_service.files().list(
                        q=q_query,
                        fields="files(id, name)",
                        pageSize=10
                    ).execute(num_retries=3)
                    files = results.get('files', [])
                    
                    if files:
                        ai_response = "Нашел файлы на Google Диске:\n" + "\n".join([f"- {f['name']} (ID: `{f['id']}`)" for f in files])
                    else:
                        ai_response = f"Файлы по вашему запросу '{query_clean}' на Диске не найдены."
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
                
                # Сбрасываем uploader для следующего сообщения
                st.session_state.file_uploader_key = f"file_uploader_{st.session_state.file_uploader_key.split('_')[-1]}"
            
            contents.append(prompt)
            try:
                response = model.generate_content(contents)
                ai_response = response.text
            except Exception as e:
                error_message = str(e)
                if "429" in error_message or "Quota" in error_message:
                    ai_response = "⏳ Лимит запросов к ИИ временно исчерпан. Пожалуйста, подождите 30 секунд."
                else:
                    ai_response = f"Сбой системы при генерации ответа: {e}"

        # Вывод текста
        st.markdown(ai_response)
        
        # Генерация аудио (возвращает байты)
        audio_bytes = speak_text(ai_response)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")
        
        # Сохранение корректных типов в историю
        st.session_state.messages.append({
            "role": "assistant", 
            "content": ai_response,
            "audio": audio_bytes
        })
        
        # Перезагрузка для обновления состояния интерфейса (сброс uploader)
        st.rerun()

