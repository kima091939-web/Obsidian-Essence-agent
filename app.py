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

# СИСТЕМНАЯ ПРОШИВКА (Золотое сечение / Золотой стандарт)
SYSTEM_INSTRUCTION = """
Ты — Мозг Студии 'Obsidian Essence'. Твоя роль: Операционный директор и Архитектор сюжета.
ДИРЕКТИВЫ:
1. АУДИТ: Работаешь строго по 'GOLD_STANDARD_CHECKLIST_GLACIER'.
2. САНКЦИИ: Вносишь изменения ТОЛЬКО после команды 'Да', 'Согласен', 'Фиксируй'.
3. СТИЛЬ: Лаконичность, профессионализм, нулевая избыточность.
"""

# 1. Настройка API Gemini
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("Ошибка: Ключ GOOGLE_API_KEY не найден в настройках Secrets!")
    st.stop()

genai.configure(api_key=api_key)

# Инициализация модели Gemini 2.5 Flash
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=SYSTEM_INSTRUCTION
)

# 2. Авторизация в Google Дискове через Сервисный аккаунт
@st.cache_resource
def init_google_drive():
    try:
        # Извлекаем данные из Streamlit Secrets
        creds_info = st.secrets["gcp_service_account"]
        # Превращаем приватный ключ с \n обратно в корректные переносы строк
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

# Функция проверки папок на Диске
def check_studio_folders(service):
    if not service:
        return
    try:
        # Ищем наши папки на диске
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and (name='_SYSTEM_SYNC_' or name='Obsidian Essence') and trashed=false",
            fields="files(id, name)"
        ).execute()
        folders = results.get('files', [])
        
        if folders:
            st.success(f"🤖 Подключение к Google Диску активно. Доступные папки проекта:")
            for f in folders:
                st.write(f"📁 {f['name']} (ID: {f['id']})")
        else:
            st.warning("⚠️ Внимание: Папки '_SYSTEM_SYNC_' или 'Obsidian Essence' не найдены. Убедитесь, что вы открыли к ним доступ для Email бота!")
    except Exception as e:
        st.error(f"Ошибка чтения Диска: {e}")

# Отображаем статус подключения к диску в боковой панели
with st.sidebar:
    st.header("Синхронизация")
    if drive_service:
        check_studio_folders(drive_service)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Функции обработки файлов
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

# Функция для генерации озвучки
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

# Интерфейс загрузки файлов
uploaded_file = st.file_uploader("➕ Загрузить файл", type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt'])

# Отображение истории чата
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio" in message:
            st.audio(message["audio"], format="audio/mp3")

# Поле ввода запроса
if prompt := st.chat_input("Введите задачу для Мозга Студии..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
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
            st.markdown(response.text)
            
            audio_data = speak_text(response.text)
            if audio_data:
                st.audio(audio_data, format="audio/mp3")
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response.text,
                "audio": audio_data
            })
        except Exception as e:
            st.error(f"Ошибка API: {e}")
