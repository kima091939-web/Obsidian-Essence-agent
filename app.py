import streamlit as st
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from gtts import gTTS
import base64

# СИСТЕМНАЯ ПРОШИВКА
SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Operational Director.
Действуй по Регламенту: 
- Нулевая избыточность (без приветствий и воды).
- 'Скелет прежде плоти': сначала анализ структуры/файла, потом рекомендации.
- Если пользователь просит найти файл, ищи точечно.
- Если файл прочитан, анализируй его содержимое строго согласно нашим Манифестам.
"""

# Настройка API
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

# ФУНКЦИЯ ОЗВУЧКИ
def speak_text(text):
    tts = gTTS(text=text, lang='ru')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    audio_bytes = fp.read()
    b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
    audio_html = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64_audio}"></audio>'
    st.markdown(audio_html, unsafe_allow_html=True)

st.set_page_config(page_title="Obsidian Essence", layout="centered")
st.title("Obsidian Essence: Brain")

# ФУНКЦИЯ ЧТЕНИЯ КОНТЕНТА
def get_file_text(file_id):
    try:
        request = drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
        return request.execute().decode('utf-8')
    except:
        return "Ошибка: не удалось прочитать этот файл."

# ЛОГИКА ПОИСКА И АНАЛИЗА
if "messages" not in st.session_state: st.session_state.messages = []

if prompt := st.chat_input("Найти файл или дай команду на анализ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        # Поиск
        if "найди" in prompt.lower() or "поиск" in prompt.lower():
            query = prompt.replace("найди", "").replace("поиск", "").strip()
            # Добавлен параметр supportsAllDrives=True для видимости всех файлов
            results = drive_service.files().list(
                q=f"name contains '{query}' and trashed=false", 
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            files = results.get('files', [])
            
            if files:
                response = "Нашел файлы:\n" + "\n".join([f"- {f['name']} (ID: `{f['id']}`)" for f in files])
            else:
                response = "Файлы не найдены."
        
        elif "прочитай" in prompt.lower():
            file_id = prompt.split()[-1].strip("`")
            content = get_file_text(file_id)
            analysis = model.generate_content(f"Проанализируй этот документ согласно регламенту:\n{content}")
            response = analysis.text
        
        else:
            response = model.generate_content(prompt).text
        
        st.markdown(response)
        speak_text(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
