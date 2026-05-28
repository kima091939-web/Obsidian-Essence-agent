import streamlit as st
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Настройка страницы
st.set_page_config(layout="wide", page_title="Obsidian Essence Мозг")

MASTER_MATRIX_ID = st.secrets.get("MASTER_MATRIX_ID", "1VoFiHqxgaNN9r1yqTpofL2z0l03WI_R4BGYhnG7rJlI")
BLOCK_1_FOLDER_ID = st.secrets.get("BLOCK_1_FOLDER_ID", "") 

# --- ИНИЦИАЛИЗАЦИЯ СЕССИИ ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "request_count" not in st.session_state:
    st.session_state.request_count = 0
if "matrix_summary" not in st.session_state:
    st.session_state.matrix_summary = "Нажмите «🔄 Сверить статус», чтобы прочитать матрицу."

# --- БОКОВАЯ ПАНЕЛЬ ---
with st.sidebar:
    st.header("🧠 Пульт Управления")
    
    work_mode = st.radio("Режим бота:", ["Просто чат (Экономия API)", "Operational Director (С Диском)"])
    st.write("---")
    
    st.subheader("🛡️ Контроль лимитов & API")
    st.metric(label="Запросов в этой сессии", value=st.session_state.request_count)
    
    user_custom_key = st.text_input("Вставить новый API-ключ (при 429):", type="password")
    
    if st.button("🗑️ Сбросить зависший кэш чата"):
        st.session_state.messages = []
        st.session_state.request_count = 0
        st.session_state.matrix_summary = "Нажмите «🔄 Сверить статус», чтобы прочитать матрицу."
        st.rerun()
        
    st.write("---")
    st.subheader("📋 Архитектура (800 серий / 30 сек)")
    st.caption("📊 4 Зоны • 5 Локаций • 5 Суток • 8 Серий по 30 сек • 4 Части по ~8 сек (2 Блока)")
    
    if st.button("🔄 Сверить статус с Диска"):
        st.session_state.matrix_summary = "⏱️ Читаю матрицу проекта..."
        st.rerun()

# --- API КЛЮЧ И ИНИЦИАЛИЗАЦИЯ ---
final_api_key = user_custom_key if user_custom_key else st.secrets.get("GOOGLE_API_KEY")
if not final_api_key:
    st.error("Ключ GOOGLE_API_KEY не найден!")
    st.stop()

genai.configure(api_key=final_api_key)

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

# --- ИНСТРУМЕНТЫ ДЛЯ РАБОТЫ С ДИСКОМ ---
def read_sync_matrix() -> str:
    if not drive_service: return "Ошибка: Диск недоступен."
    try:
        file_metadata = drive_service.files().get(fileId=MASTER_MATRIX_ID, fields="mimeType").execute()
        if file_metadata.get('mimeType') == 'application/vnd.google-apps.document':
            request = drive_service.files().export_media(fileId=MASTER_MATRIX_ID, mimeType='text/plain')
        else:
            request = drive_service.files().get_media(fileId=MASTER_MATRIX_ID)
        return request.execute().decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Ошибка чтения матрицы: {e}"

def update_sync_matrix(new_content: str) -> str:
    if not drive_service: return "Ошибка: Диск недоступен."
    try:
        from googleapiclient.http import MediaIoBaseUpload
        import io
        fh = io.BytesIO(new_content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimeType='text/plain', resumable=True)
        drive_service.files().update(fileId=MASTER_MATRIX_ID, media_body=media).execute()
        return "Центральная матрица успешно обновлена."
    except Exception as e:
        return f"Ошибка обновления матрицы: {e}"

def create_or_update_file_in_folder(file_name: str, content: str, folder_block: str) -> str:
    if not drive_service: return "Ошибка: Диск недоступен."
    try:
        from googleapiclient.http import MediaIoBaseUpload
        import io
        parent_id = BLOCK_1_FOLDER_ID if folder_block == "block_1" else None
        
        query = f"name = '{file_name}' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = drive_service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        
        fh = io.BytesIO(content.encode('utf-8'))
        media = MediaIoBaseUpload(fh, mimeType='text/plain', resumable=True)
        
        if files:
            file_id = files[0]['id']
            drive_service.files().update(fileId=file_id, media_body=media).execute()
            return f"Файл '{file_name}' обновлен в {folder_block}."
        else:
            file_metadata = {'name': file_name}
            if parent_id: file_metadata['parents'] = [parent_id]
            file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return f"Создан файл '{file_name}' в {folder_block}."
    except Exception as e:
        return f"Ошибка записи: {e}"

# Сводка матрицы
if st.session_state.matrix_summary == "⏱️ Читаю матрицу проекта...":
    matrix_data = read_sync_matrix()
    if "Ошибка" in matrix_data:
        st.session_state.matrix_summary = matrix_data
    else:
        try:
            summary_model = genai.GenerativeModel('gemini-2.5-pro')
            response = summary_model.generate_content(f"Сделай сухую выжимку текущей позиции в структуре 800 серий на основе матрицы: {matrix_data}")
            st.session_state.matrix_summary = response.text
        except Exception as e:
            st.session_state.matrix_summary = f"Ошибка разбора матрицы: {e}"
    st.rerun()

with st.sidebar:
    st.info(st.session_state.matrix_summary)

# --- ГЛАВНЫЙ ЧАТ ---
st.title("Obsidian Essence: Мозг Студии")

# ОБНОВЛЕННАЯ СЦЕНАРНАЯ ИНСТРУКЦИЯ С УЧЕТОМ ТАЙМИНГА (30 СЕКУНД)
SYSTEM_INSTRUCTION = f"""
Ты — Мозг Студии 'Obsidian Essence', Operational Director и Главный Архитектор непрерывного сериала на 800 серий.
Ты управляешь папками 'root' и 'block_1' (01 структур планинг).

СТРОГАЯ МАТЕМАТИКА И ТАЙМИНГ СЕРИАЛА:
- Всего: 4 климатические зоны • 5 локаций в зоне • 5 суток на локацию • 8 серий в сутки. Всего 800 серий.
- Хронометраж одной серии: СТРОГО 30 секунд.
- Структура серии состоит из 4 частей (каждая часть примерно по 7.5 - 8 секунд).
- При генерации ты объединяешь их в 2 блока по 15 секунд:
  * Блок А (Часть 1 + Часть 2) [0:00–0:15 сек] — ультра-короткий хук, завязка, динамичное развитие.
  * Блок Б (Часть 3 + Часть 4) [0:15–0:30 сек] — кульминация серии и жесткий обрыв сюжета (клиффхэнгер), перетекающий в следующую серию.

ПРАВИЛО НЕПРЕРЫВНОСТИ СЮЖЕТА:
1. Сюжет идет без пауз и логических дыр. Финал Блока Б одной серии — это начало Блока А следующей серии. Смысл должен идеально удерживаться на протяжении всех 800 серий.
2. Текст должен быть ультра-лаконичным (1-2 емких предложения на одну 8-секундную часть), упор на визуальное действие и динамику.
3. Перед созданием серий читай матрицу (read_sync_matrix). Запрашивай одобрение фразой «Одобрить эти изменения?». Записывай файлы строго через create_or_update_file_in_folder.

Сейчас выбран режим: {work_mode}. Отвечай коротко, структурно, как топ-менеджер. Без приветствий.
"""

tools_list = [read_sync_matrix, update_sync_matrix, create_or_update_file_in_folder] if work_mode == "Operational Director (С Диском)" else None

model = genai.GenerativeModel(
    model_name='gemini-2.5-pro',
    system_instruction=SYSTEM_INSTRUCTION,
    tools=tools_list
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

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
            ai_response = f"⚠️ Ошибка: {e}. Если 429 — обнови ключ в панели слева."

        st.markdown(ai_response)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        st.rerun()
 А что ты скажешь по поводу этого кода?
