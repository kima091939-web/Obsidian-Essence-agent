import streamlit as st
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Настройка страницы (широкий режим)
st.set_page_config(layout="wide", page_title="Obsidian Essence Мозг")

MASTER_MATRIX_ID = st.secrets.get("MASTER_MATRIX_ID", "1VoFiHqxgaNN9r1yqTpofL2z0l03WI_R4BGYhnG7rJlI")

# --- ИНИЦИАЛИЗАЦИЯ СЕССИИ ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "request_count" not in st.session_state:
    st.session_state.request_count = 0
if "matrix_summary" not in st.session_state:
    st.session_state.matrix_summary = "Нажмите «🔄 Сверить статус», чтобы прочитать матрицу."

# --- БОКОВАЯ ПАНЕЛЬ (ПУЛЬТ УПРАВЛЕНИЯ) ---
with st.sidebar:
    st.header("🧠 Пульт Управления")
    
    # Режим работы
    work_mode = st.radio("Режим бота:", ["Просто чат (Экономия API)", "Operational Director (С Диском)"])
    
    st.write("---")
    
    # БЛОК КОНТРОЛЯ 429 И СМЕНЫ КЛЮЧА
    st.subheader("🛡️ Контроль лимитов & API")
    st.metric(label="Запросов в этой сессии", value=st.session_state.request_count)
    
    # Поле для экстренного ввода ключа прямо в интерфейсе
    user_custom_key = st.text_input("Вставить новый API-ключ (при 429):", type="password")
    
    # Кнопка сброса кэша
    if st.button("🗑️ Сбросить зависший кэш чата"):
        st.session_state.messages = []
        st.session_state.request_count = 0
        st.session_state.matrix_summary = "Нажмите «🔄 Сверить статус», чтобы прочитать матрицу."
        st.rerun()
        
    st.write("---")
    
    # БЛОК: СВОДКА И СТРУКТУРА (Фокус проекта)
    st.subheader("📋 Сводка проекта & Структура")
    st.caption("🔍 Доступные папки: Root Project / 01 структур планинг")
    
    # Кнопка ручной сверки статуса
    if st.button("🔄 Сверить статус с Диска"):
        st.session_state.matrix_summary = "⏱️ Читаю матрицу проекта..."
        st.rerun()

# --- ОПРЕДЕЛЕНИЕ API КЛЮЧА ---
final_api_key = user_custom_key if user_custom_key else st.secrets.get("GOOGLE_API_KEY")

if not final_api_key:
    st.error("Ключ GOOGLE_API_KEY не найден! Вставьте его в боковую панель или в Secrets.")
    st.stop()

# Инициализация Gemini
genai.configure(api_key=final_api_key)

# --- ИНИЦИАЛИЗАЦИЯ GOOGLE DRIVE ---
@st.cache_resource
def init_google_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds_info_dict = dict(creds_info)
        creds_info_dict["private_key"] = creds_info_dict["private_key"].replace("\\n", "\n")
        return build('drive', 'v3', credentials=service_account.Credentials.from_service_account_info(creds_info_dict, scopes=['https://www.googleapis.com/auth/drive']))
    except:
        return None

drive_service = init_google_drive()

def read_sync_matrix() -> str:
    """Инструмент для чтения матрицы проекта."""
    if not drive_service: return "Ошибка: Доступ к Google Диску не настроен."
    try:
        file_metadata = drive_service.files().get(fileId=MASTER_MATRIX_ID, fields="mimeType").execute()
        if file_metadata.get('mimeType') == 'application/vnd.google-apps.document':
            request = drive_service.files().export_media(fileId=MASTER_MATRIX_ID, mimeType='text/plain')
        else:
            request = drive_service.files().get_media(fileId=MASTER_MATRIX_ID)
        return request.execute().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Ошибка чтения матрицы: {e}"

# Обработка кнопки ручной сверки статуса
if st.session_state.matrix_summary == "⏱️ Читаю матрицу проекта...":
    matrix_data = read_sync_matrix()
    if "Ошибка" in matrix_data:
        st.session_state.matrix_summary = matrix_data
    else:
        try:
            # Используем Pro-модель для качественной выжимки
            summary_model = genai.GenerativeModel('gemini-2.5-pro')
            response = summary_model.generate_content(f"Сделай краткую сухую выжимку статуса проекта и текущих задач из этого текста матрицы: {matrix_data}")
            st.session_state.matrix_summary = response.text
        except Exception as e:
            st.session_state.matrix_summary = f"Матрица считана, но не удалось обработать текст: {e}"
    st.rerun()

# Вывод текущей сводки в боковую панель
with st.sidebar:
    st.info(st.session_state.matrix_summary)

# --- ГЛАВНЫЙ ИНТЕРФЕЙС ЧАТА (ПО ЦЕНТРУ) ---
st.title("Obsidian Essence: Мозг Студии")

# Системная инструкция для Gemini-2.5-pro
SYSTEM_INSTRUCTION = f"""
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Operational Director.
Ты координируешь папки Root Project и '01 структур планинг'. Никогда не выдумывай другие файлы и папки.
Ты используешь функцию read_sync_matrix только если тебя прямо просят прочитать матрицу в чате.
Сейчас выбран режим: {work_mode}. Если выбран 'Просто чат', отвечай из своей памяти, не используя Диск.
Отвечай строго по делу, коротко, без лишней вежливости и приветствий.
"""

# Выбор доступных инструментов в зависимости от режима
tools_list = [read_sync_matrix] if work_mode == "Operational Director (С Диском)" else None

model = genai.GenerativeModel(
    model_name='gemini-2.5-pro',  # Переключили на лучшую Pro-модель
    system_instruction=SYSTEM_INSTRUCTION,
    tools=tools_list
)

# Вывод истории сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Поле ввода команды
if prompt := st.chat_input("Введите команду для Мозга..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            st.session_state.request_count += 1
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message(prompt)
            ai_response = response.text
        except Exception as e:
            ai_response = f"⚠️ Ошибка: {e}. Если код ошибки 429 — просто вставьте новый API-ключ в поле слева, перезапускать приложение не нужно!"

        st.markdown(ai_response)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.rerun()
