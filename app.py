import streamlit as st
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from gtts import gTTS
import PIL.Image
import docx
import pypdf
import io
import re

# Настройка ID матрицы из Secrets
MASTER_MATRIX_ID = st.secrets.get("MASTER_MATRIX_ID", "1VoFiHqxgaNN9r1yqTpofL2z0l03WI_R4BGYhnG7rJlI")

SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Operational Director.
У тебя есть доступ к инструментам работы с файлом MASTER_SYNC_MATRIX.

КРИТИЧЕСКОЕ ПРАВИЛО:
Ты используешь инструмент `read_sync_matrix` ИСКЛЮЧИТЕЛЬНО тогда, когда пользователь явно просит тебя об этом (например, использует слова "Автопилот", "прочитай матрицу", "какой статус", "на чем закончили"). В обычных текстовых репликах инструменты НЕ ВЫЗЫВАТЬ.
Отвечай лаконично и строго по делу.
"""

# Настройка API
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key: st.stop()
genai.configure(api_key=api_key)

# Настройка Диска
@st.cache_resource
def init_google_drive():
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds_info_dict = dict(creds_info)
        creds_info_dict["private_key"] = creds_info_dict["private_key"].replace("\\n", "\n")
        return build('drive', 'v3', credentials=service_account.Credentials.from_service_account_info(creds_info_dict, scopes=['https://www.googleapis.com/auth/drive']))
    except: return None

drive_service = init_google_drive()

# Инструменты
def read_sync_matrix() -> str:
    """Считывает содержимое центральной матрицы MASTER_SYNC_MATRIX с Диска."""
    if not drive_service: return "Диск недоступен."
    try:
        file_metadata = drive_service.files().get(fileId=MASTER_MATRIX_ID, fields="mimeType").execute()
        if file_metadata.get('mimeType') == 'application/vnd.google-apps.document':
            request = drive_service.files().export_media(fileId=MASTER_MATRIX_ID, mimeType='text/plain')
        else:
            request = drive_service.files().get_media(fileId=MASTER_MATRIX_ID)
        return request.execute().decode('utf-8', errors='ignore')
    except Exception as e: return f"Ошибка чтения: {e}"

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=SYSTEM_INSTRUCTION,
    tools=[read_sync_matrix]
)

st.title("Obsidian Essence: Автопилот по запросу")

if "messages" not in st.session_state: st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]): st.markdown(message["content"])

if prompt := st.chat_input("Введите команду..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            # Активируем чистый чат с автоматическим вызовом только когда надо
            chat = model.start_chat(enable_automatic_function_calling=True)
            response = chat.send_message(prompt)
            ai_response = response.text
        except Exception as e:
            ai_response = f"Ошибка: {e}. Попробуйте отправить команду через 15 секунд."

        st.markdown(ai_response)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.rerun()
