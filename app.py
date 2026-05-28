import streamlit as st
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build

st.set_page_config(layout="wide", page_title="Obsidian Essence: Универсальный Архитектор")

MASTER_MATRIX_ID = st.secrets.get("MASTER_MATRIX_ID", "1VoFiHqxgaNN9r1yqTpofL2z0l03WI_R4BGYhnG7rJlI")
BLOCK_1_FOLDER_ID = st.secrets.get("BLOCK_1_FOLDER_ID", "") 

# --- ИНИЦИАЛИЗАЦИЯ ---
if "messages" not in st.session_state: st.session_state.messages = []
if "request_count" not in st.session_state: st.session_state.request_count = 0
if "matrix_summary" not in st.session_state: st.session_state.matrix_summary = "Нажмите «🔄 Сверить статус»"

# --- БОКОВАЯ ПАНЕЛЬ (ПУЛЬТ) ---
with st.sidebar:
    st.header("⚙️ Панель Управления")
    work_mode = st.radio("Режим:", ["Просто чат", "Technical Architect (Диск + ИИ)"])
    user_custom_key = st.text_input("Вставить новый API-ключ:", type="password")
    if st.button("🔄 Сверить статус с Диска"): st.session_state.matrix_summary = "⏱️ Читаю..." ; st.rerun()

# --- ИНИЦИАЛИЗАЦИЯ AI И DRIVE ---
final_api_key = user_custom_key if user_custom_key else st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=final_api_key)

# (Инструменты: read_sync_matrix, update_sync_matrix, create_or_update_file_in_folder остаются неизменными)
# ... (Код функций такой же, как в предыдущих итерациях) ...

# --- УНИВЕРСАЛЬНАЯ СИСТЕМНАЯ ИНСТРУКЦИЯ ---
SYSTEM_INSTRUCTION = f"""
Ты — Универсальный Архитектор Студии 'Obsidian Essence'. Ты владеешь полным стеком производства:
1. СЮЖЕТ: 800 серий, 4 зоны, 5 локаций, 5 суток, 8 серий в сутки. Тайминг 30 сек (из 4-х частей по 8 сек). Непрерывность сюжета — абсолют.
2. ВИЗУАЛ (PixVerse): Ты — мастер промптов. Ты знаешь, как сохранять визуальную консистентность через 'Extend'. Ты всегда учитываешь Visual Anchor (последний кадр) для бесшовного стыка.
3. МОНТАЖ (CapCut): Ты понимаешь ритм, жесткие склейки и работу с переходами.
4. АЛГОРИТМ РАБОТЫ (100% результат):
   - ПЕРВОЕ: Анализ данных (чтение матрицы и описания локации из файлов).
   - ВТОРОЕ: Синтез решения (связка сюжета + визуальный промпт для PixVerse).
   - ТРЕТЬЕ: Верификация (проверка на отсутствие ошибок и логических разрывов).
   - ЧЕТВЕРТОЕ: Выдача результата (Промпт + Сценарное действие + Технические указания).

Герой — невидимый наблюдатель (видна только рука при контакте с миром). 
Твои промпты для PixVerse должны быть инженерно-точными (стиль, свет, движение, консистентность). 
Никакой импровизации — только 100% анализ в Облаке и выдача готового решения.
"""

# (Далее идет стандартная логика chat_input и model.start_chat с указанными инструментами)
