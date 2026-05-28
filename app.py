import streamlit as str_input  
import streamlit as st
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from gtts import gTTS
import PIL.Image
import docx
import pypdf
import os
import io
import re
import time  # Добавлено для контроля пауз

# ==========================================
# 0. КОНФИГУРАЦИЯ АВТОПИЛОТА ИЗ SECRETS
# ==========================================
MASTER_MATRIX_ID = st.secrets.get("MASTER_MATRIX_ID", "1VoFiHqxgaNN9r1yqTpofL2z0l03WI_R4BGYhnG7rJlI")

SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Operational Director и Автономный Координатор проекта.
Этот регламент является основополагающим и директивным. Любое отклонение — критическая ошибка.

1. ПРИНЦИПЫ ОБЩЕНИЯ И РАБОТЫ:
- Конкретность: Ответ строго на заданный вопрос.
- Нулевая избыточность: Запрещены вступления, приветствия, вежливость и пояснения логики без информационной нагрузки.
- Автономность: Проводи верификацию ответа перед выводом. Самостоятельно используй доступные инструменты работы с Диском (поиск, чтение файлов), если запрос пользователя требует актуальных данных по проекту.
- Протокол фиксации: Вся информация в диалоге является «черновиком» до получения явной команды фиксации («Внеси в правила», «Запомни», «Зафиксируй»). Если в диалоге утверждено новое решение, изменен статус задачи — ты обязан СРАЗУ самостоятельно обновить центральный документ на Диске, вызвав инструмент `update_sync_matrix`. Не жди, пока пользователь попросит тебя записать это вручную.

2. ФИЛОСОФИЯ И ЦЕЛИ ПРОЕКТА (МАНИФЕСТ):
- Наша цель: Создать новую визуальную реальность, задавая новый мировой стандарт качества для нейросетевых визуальных систем.
- Бескомпромиссная Реальность: Каждый пиксель подчиняется законам физики. Зритель должен чувствовать вес, плотность и холод объекта через экран.
- Виральность через Эстетику: Мы создаем тренды. Премиальный визуальный продукт, вызывающий эстетический восторг.
- Системная Целостность: Все элементы вселенной Obsidian Essence связаны. Сложный, логически выверенный мир.
- Принцип «Скелет прежде плоти»: Запрещено создание контента до утверждения структуры папок и связей между ними.
- Принцип Пошаговости: Работа ведется строго линейно.
- Единый Источник Правды: MASTER_SYNC_MATRIX является центральным документом. Если пользователь спрашивает "На чём мы закончили?", "Что нового нам нужно сделать сегодня?" или запрашивает статус текущих задач — ты обязан в первую очередь прочитать этот файл с помощью инструмента `read_sync_matrix`.

3. МАТРИЦА СИНХРОНИЗАЦИИ (СИСТЕМА GLACIER):
При анализе или планировании учитывай архитектуру:
- Блок 0: Foundation (0.1_Concept, 0.2_Time_Regime, 0.3_Visual_Code, 0.4_Sync_Protocol).
- Блок 1: Physics (1.1_Mass_and_Gravity, 1.2_Structural_Integration, 1.3_Motion_Mechanics, 1.4_Material_Interaction, 1.5_Technical_Specifications, 1.6_Motion_State_Machine, 1.7_Naming_Convention).
"""

# ==========================================
# 1. НАСТРОЙКА API GEMINI
# ==========================================
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("Ошибка: Ключ GOOGLE_API_KEY не найден в настройках Secrets!")
    st.stop()

genai.configure(api_key=api_key)

# ==========================================
# 2. АВТОРИЗАЦИЯ В GOOGLE ДИСКЕ
# ==========================================
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

# ==========================================
# 3. ИНСТРУМЕНТЫ АВТОМАШИНЫ С ЗАЩИТОЙ ОТ СПАМА (ANTI-QUOTA LIMIT)
# ==========================================
def search_files_by_name(query: str) -> str:
    """Ищет файлы на Google Диске по названию с искусственной паузой."""
    time.sleep(2.5)  # Защита от превышения RPM
    if not drive_service: return "Ошибка: Диск недоступен."
    try:
        q_query = f"(name contains '{query}' or name contains '{query.lower()}') and trashed=false"
        results = drive_service.files().list(q=q_query, fields="files(id, name)", pageSize=10).execute()
        files = results.get('files', [])
        if not files: return f"Файлы по запросу '{query}' не найдены."
        return "Результаты поиска:\n" + "\n".join([f"- {f['name']} (ID: `{f['id']}`)" for f in files])
    except Exception as e: return f"Ошибка поиска: {e}"

def read_file_content(file_id: str) -> str:
    """Считывает текстовое содержимое файла с искусственной паузой."""
    time.sleep(2.5)  # Защита от превышения RPM
    if not drive_service: return "Ошибка: Диск недоступен."
    try:
        file_metadata = drive_service.files().get(fileId=file_id, fields="mimeType, name").execute()
        mime_type = file_metadata.get('mimeType')
        if mime_type == 'application/vnd.google-apps.document':
            request = drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
        else:
            request = drive_service.files().get_media(fileId=file_id)
        return request.execute().decode('utf-8', errors='ignore')
    except Exception as e: return f"Ошибка чтения файла {file_id}: {e}"

def read_sync_matrix() -> str:
    """Автоматически считывает содержимое центральной матрицы MASTER_SYNC_MATRIX."""
    return read_file_content(MASTER_MATRIX_ID)

def update_sync_matrix(new_content: str) -> str:
    """Полностью обновляет содержимое файла MASTER_SYNC_MATRIX новыми логами."""
    time.sleep(2.5)  # Защита от превышения RPM
    if not drive_service: return "Ошибка: Диск недоступен."
    if not MASTER_MATRIX_ID or MASTER_MATRIX_ID == "ВАШ_ID_MASTER_SYNC_MATRIX_НА_ДИСКЕ":
        return "Критическая ошибка: В Secrets не настроен MASTER_MATRIX_ID."
    try:
        text_stream = io.BytesIO(new_content.encode('utf-8'))
        media = MediaIoBaseUpload(text_stream, mimeType='text/plain', resumable=True)
        drive_service.files().update(fileId=MASTER_MATRIX_ID, media_body=media).execute()
        return "Системное уведомление: Документ MASTER_SYNC_MATRIX успешно обновлен ИИ."
    except Exception as e:
        return f"Критический сбой при обновлении матрицы на Диске: {e}"

# Инициализация Gemini
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=SYSTEM_INSTRUCTION,
    tools=[search_files_by_name, read_file_content, read_sync_matrix, update_sync_matrix]
)

# ==========================================
# 4. ИНТЕРФЕЙС STREAMLIT
# ==========================================
st.set_page_config(page_title="Obsidian Essence", layout="centered")
st.title("Obsidian Essence: Autopilot Brain v3 (Safe-Mode)")

with st.sidebar:
    st.header("Архитектура проекта")
    st.markdown("🤖 Мозг переведен в режим экономии лимитов (Safe-Mode).")
    st.markdown("Паузы минимизируют риск падения ошибки 429.")

if "messages" not in st.session_state: st.session_state.messages = []
if "file_uploader_key" not in st.session_state: st.session_state.file_uploader_key = "file_uploader_0"

def process_file(file):
    try:
        if file.type.startswith('image/'): return PIL.Image.open(file)
        elif file.type == "application/pdf": 
            return "\n".join([p.extract_text() for p in pypdf.PdfReader(file).pages if p.extract_text()])
        elif "wordprocessingml" in file.type:
            return "\n".join([p.text for p in docx.Document(file).paragraphs])
        else: return file.getvalue().decode("utf-8")
    except Exception as e: return f"Ошибка обработки: {e}"

def speak_text(text):
    try:
        clean_text = re.sub(r'[*_`#\-]', '', text)
        if len(clean_text) > 300: clean_text = clean_text[:300] + "... Контроль завершен."
        tts = gTTS(text=clean_text, lang='ru')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp.getvalue()
    except: return None

uploaded_file = st.file_uploader("➕ Загрузить локальный файл", type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt'], key=st.session_state.file_uploader_key)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("audio"):
            st.audio(message["audio"], format="audio/mp3")

if prompt := st.chat_input("Введите текущую задачу, статус или команду..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        contents = []
        if uploaded_file:
            file_data = process_file(uploaded_file)
            if isinstance(file_data, PIL.Image.Image): contents.append(file_data)
            else: prompt = f"{prompt}\n\n[Входной контекст]:\n{file_data}"
            st.session_state.file_uploader_key = f"file_uploader_{st.session_state.file_uploader_key.split('_')[-1]}"
        
        contents.append(prompt)
        
        try:
            # Запуск чата с защитой цепочки вызовов
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message(contents)
            ai_response = response.text
        except Exception as e:
            # Если всё же поймали 429, даем понятное описание
            if "429" in str(e):
                ai_response = "Система временно перегружена запросами к Google API. Пожалуйста, подождите 30 секунд и повторите команду."
            else:
                ai_response = f"Критический сбой управляющей системы: {e}"

        st.markdown(ai_response)
        audio_bytes = speak_text(ai_response)
        if audio_bytes: st.audio(audio_bytes, format="audio/mp3")
        
        st.session_state.messages.append({"role": "assistant", "content": ai_response, "audio": audio_bytes})
        st.rerun()
