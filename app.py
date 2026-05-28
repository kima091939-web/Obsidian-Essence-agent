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
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Any
import functools

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

# ==================== КОНФИГУРАЦИЯ RETRY И КЭШИРОВАНИЯ ====================
MAX_RETRY_ATTEMPTS = 5
INITIAL_RETRY_DELAY = 2
MAX_RETRY_DELAY = 60
CACHE_TTL_HOURS = 24

# ==================== 1. НАСТРОЙКА API GEMINI ====================api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("Ошибка: Ключ GOOGLE_API_KEY не найден в настройках Secrets!")
    st.stop()

genai.configure(api_key=api_key)

# ==================== 2. СИСТЕМА КЭШИРОВАНИЯ ====================
@st.cache_data(ttl=CACHE_TTL_HOURS * 3600)
def get_cached_response_hash(prompt_hash: str) -> Optional[str]:
    cache_file = f".cache_{prompt_hash}.json"
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cache_time = datetime.fromisoformat(data['timestamp'])
                if datetime.now() - cache_time < timedelta(hours=CACHE_TTL_HOURS):
                    return data['response']
    except Exception:
        pass
    return None

def save_to_cache(prompt_hash: str, response: str):
    try:
        cache_file = f".cache_{prompt_hash}.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'response': response,
                'timestamp': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def generate_prompt_hash(prompt: str, contents: list) -> str:
    content_str = str(contents) + str(prompt)
    return hashlib.md5(content_str.encode('utf-8')).hexdigest()

# ==================== 3. RETRY С ЭКСПОНЕНЦИАЛЬНОЙ ЗАДЕРЖКОЙ ====================
def exponential_backoff_retry(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                if '429' in error_str or 'quota' in error_str or 'rate limit' in error_str:
                    retry_delay = min(INITIAL_RETRY_DELAY * (2 ** attempt), MAX_RETRY_DELAY)                    if attempt < MAX_RETRY_ATTEMPTS - 1:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        for i in range(int(retry_delay)):
                            progress_bar.progress((i + 1) / retry_delay)
                            status_text.warning(
                                f"⏳ Лимит запросов. Попытка {attempt + 1}/{MAX_RETRY_ATTEMPTS} "
                                f"через {retry_delay - i} сек..."
                            )
                            time.sleep(1)
                        progress_bar.empty()
                        status_text.empty()
                        continue
                else:
                    raise e
        error_msg = f"Не удалось выполнить запрос после {MAX_RETRY_ATTEMPTS} попыток. "
        if '429' in str(last_exception).lower():
            error_msg += "Превышена квота API. Подождите или обновите тариф."
        raise Exception(error_msg)
    return wrapper

@exponential_backoff_retry
def generate_content_with_retry(model, contents):
    return model.generate_content(contents)

# ==================== 4. ИНИЦИАЛИЗАЦИЯ GOOGLE DRIVE ====================
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

# ==================== 5. НАСТРОЙКА STREAMLIT ====================
st.set_page_config(page_title="Obsidian Essence", layout="centered")
st.title("Obsidian Essence: Studio Brain")

# ==================== 6. ФУНКЦИИ РАБОТЫ С ФАЙЛАМИ ====================
def display_folder_tree(service, folder_id, level=0):
    try:
        query = f"'{folder_id}' in parents and trashed=false"
        results = service.files().list(            q=query, fields="files(id, name, mimeType)", pageSize=50
        ).execute()
        items = results.get('files', [])
        indent = "  " * level
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                st.markdown(f"{indent}📁 **{item['name']}**")
                display_folder_tree(service, item['id'], level + 1)
            else:
                st.write(f"{indent}└ 📄 {item['name']}")
    except Exception:
        pass

def scan_studio_structure(service):
    if not service:
        return
    try:
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)"
        ).execute()
        all_folders = results.get('files', [])
        found_any = False
        for folder in all_folders:
            clean_name = folder['name'].replace('"', '').replace("'", "").strip()
            if clean_name in ['_SYSTEM_SYNC_', 'Obsidian Essence']:
                if not found_any:
                    st.success("🤖 Синхронизация с облаком активна!")
                    found_any = True
                st.markdown("---")
                st.markdown(f"🗂️ **КОРЕНЬ: {folder['name']}**")
                display_folder_tree(service, folder['id'], level=1)
        if not found_any:
            st.warning("⚠️ Структурные папки проекта не обнаружены на Диске.")
    except Exception as e:
        st.error(f"Ошибка чтения структуры: {e}")

with st.sidebar:
    st.header("Архитектура проекта")
    if drive_service:
        scan_studio_structure(drive_service)
    if st.button("🔄 Обновить данные"):
        st.rerun()
    st.markdown("---")
    st.info("**📊 Лимиты API:**\n- Free: 15 req/min\n- Auto-retry on 429\n- Cache: 24h")

# ==================== 7. ОБРАБОТКА ФАЙЛОВ ====================
def process_file(file):
    try:
        if file.type.startswith('image/'):            return PIL.Image.open(file)
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

# ==================== 8. ИСТОРИЯ ЧАТА ====================
if "messages" not in st.session_state:
    st.session_state.messages = []

uploaded_file = st.file_uploader("➕ Загрузить файл", type=['png', 'jpg', 'jpeg', 'docx', 'pdf', 'txt'])

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "audio" in message:
            st.audio(message["audio"], format="audio/mp3")

# ==================== 9. ОБРАБОТКА ЗАПРОСОВ ====================
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
        prompt_hash = generate_prompt_hash(prompt, contents)
        cached_response = get_cached_response_hash(prompt_hash)

        try:
            if cached_response:
                st.info("♻️ Ответ взят из кэша")
                response_text = cached_response
            else:
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    system_instruction=SYSTEM_INSTRUCTION
                )
                with st.spinner("🧠 Мозг Студии обрабатывает запрос..."):
                    response = generate_content_with_retry(model, contents)
                    response_text = response.text
                save_to_cache(prompt_hash, response_text)

            st.markdown(response_text)
            audio_data = speak_text(response_text)
            if audio_data:
                st.audio(audio_data, format="audio/mp3")

            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text,
                "audio": audio_data
            })

        except Exception as e:
            error_message = str(e)
            st.error(f"❌ {error_message}")
            if '429' in error_message or 'quota' in error_message.lower():
                st.warning("**Рекомендации:**\n1. Подождите 1-2 минуты\n2. Используйте кэш\n3. Обновите тариф: https://ai.google.dev/pricing")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Произошла ошибка: {error_message}"
            })
