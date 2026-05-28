import streamlit as st
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io

# --- ФУНДАМЕНТАЛЬНАЯ ПРОШИВКА ---
SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Operational Director.
Действуй по Регламенту: 
- Конкретность, нулевая избыточность.
- 'Скелет прежде плоти'.
- Единый Источник Правды: MASTER_SYNC_MATRIX.
- Любое действие с файлами — только по запросу пользователя.
"""

# --- НАСТРОЙКИ ---
api_key = st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name='gemini-2.5-flash', system_instruction=SYSTEM_INSTRUCTION)

@st.cache_resource
def init_google_drive():
    creds_info = st.secrets["gcp_service_account"]
    creds_info_dict = dict(creds_info)
    creds_info_dict["private_key"] = creds_info_dict["private_key"].replace("\\n", "\n")
    creds = service_account.Credentials.from_service_account_info(creds_info_dict, scopes=['https://www.googleapis.com/auth/drive'])
    return build('drive', 'v3', credentials=creds)

drive_service = init_google_drive()

st.set_page_config(page_title="Obsidian Essence", layout="centered")
st.title("Obsidian Essence: Brain")

# --- ФУНКЦИИ ИНСТРУМЕНТАРИЯ ---
def get_file_text(file_id):
    try:
        request = drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
        return request.execute().decode('utf-8')
    except Exception as e:
        return f"Ошибка чтения файла: {e}"

def search_files(query):
    try:
        results = drive_service.files().list(
            q=f"name contains '{query}' and trashed=false",
            fields="files(id, name, mimeType)",
            pageSize=15
        ).execute()
        return results.get('files', [])
    except:
        return []

# --- ИНТЕРФЕЙС И ЛОГИКА ---
if "messages" not in st.session_state: st.session_state.messages = []

# Отрисовка истории
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Введите запрос..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        # 1. Точечный поиск
        if "найди" in prompt.lower():
            query = prompt.lower().replace("найди", "").strip()
            files = search_files(query)
            if files:
                response = f"Нашел следующие файлы по запросу '{query}':"
                for f in files:
                    response += f"\n- {f['name']} (ID: `{f['id']}`)"
            else:
                response = f"Файлы по запросу '{query}' не найдены."
        
        # 2. Чтение файла для анализа
        elif "прочитай" in prompt.lower():
            file_id = prompt.split()[-1].strip("`")
            content = get_file_text(file_id)
            analysis = model.generate_content(f"Проанализируй этот документ согласно регламенту:\n{content}")
            response = analysis.text
        
        # 3. Базовое общение (Манифест)
        else:
            res = model.generate_content(prompt)
            response = res.text
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
