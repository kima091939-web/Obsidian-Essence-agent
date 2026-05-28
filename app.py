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

# СИСТЕМНАЯ ПРОШИВКА (ИНТЕГРИРОВАННЫЕ РЕГЛАМЕНТ И МАНИФЕСТ)
SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Operational Director и Архитектор сюжета.
Действуй строго по регламенту:
1. Конкретность и нулевая избыточность (без приветствий и воды).
2. 'Скелет прежде плоти': анализ структуры перед созданием контента.
3. Манифест: качество, физическая достоверность, системная целостность.
4. Протокол фиксации: информация становится законом только после команды 'Зафиксируй'.
"""

# Настройка API
api_key = st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name='gemini-2.5-flash', system_instruction=SYSTEM_INSTRUCTION)

# Инициализация Drive
@st.cache_resource
def init_google_drive():
    creds_info = st.secrets["gcp_service_account"]
    creds_info_dict = dict(creds_info)
    creds_info_dict["private_key"] = creds_info_dict["private_key"].replace("\\n", "\n")
    scopes = ['https://www.googleapis.com/auth/drive']
    creds = service_account.Credentials.from_service_account_info(creds_info_dict, scopes=scopes)
    return build('drive', 'v3', credentials=creds)

drive_service = init_google_drive()

st.set_page_config(page_title="Obsidian Essence", layout="centered")
st.title("Obsidian Essence: Studio Brain")

# Функция чтения контента файла с Диска
def read_file_content(file_id, mime_type):
    try:
        if mime_type == 'application/vnd.google-apps.document':
            # Для Google Docs используем экспорт
            request = drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
            return request.execute().decode('utf-8')
        else:
            # Для других форматов (txt, pdf)
            content = drive_service.files().get_media(fileId=file_id).execute()
            return "Файл успешно считан. Данные готовы к анализу."
    except Exception as e:
        return f"Ошибка чтения: {e}"

# Глубокое сканирование и вывод структуры
def display_folder_tree(service, folder_id, level=0):
    query = f"'{folder_id}' in parents and trashed=false"
    items = service.files().list(q=query, fields="files(id, name, mimeType)").execute().get('files', [])
    
    indent = "  " * level
    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            st.markdown(f"{indent}📁 **{item['name']}**")
            display_folder_tree(service, item['id'], level + 1)
        else:
            st.write(f"{indent}└ 📄 {item['name']} (ID: {item['id']})") # ID нужен для чтения

# Боковая панель
with st.sidebar:
    st.header("Архитектура проекта")
    if drive_service:
        # Упрощенное сканирование
        scan_results = drive_service.files().list(q="mimeType='application/vnd.google-apps.folder' and trashed=false", fields="files(id, name)").execute()
        for folder in scan_results.get('files', []):
            if folder['name'] in ['_SYSTEM_SYNC_', 'Obsidian Essence']:
                st.markdown(f"🗂️ **{folder['name']}**")
                display_folder_tree(drive_service, folder['id'], level=1)
    if st.button("🔄 Обновить"): st.rerun()

# Чат
if "messages" not in st.session_state: st.session_state.messages = []

# Логика обработки запроса (включая чтение по ID)
if prompt := st.chat_input("Введите задачу или ID файла для анализа..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        # Если пользователь просит прочитать файл по его ID
        if "читать " in prompt.lower():
            file_id = prompt.split()[-1]
            content = read_file_content(file_id, 'application/vnd.google-apps.document')
            prompt = f"Проанализируй этот документ согласно регламенту:\n{content}"
            
        response = model.generate_content(prompt)
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
