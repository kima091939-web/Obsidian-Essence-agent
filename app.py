import json
import tempfile
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from ai_engine import StudioBrain
from drive_manager import DriveManager

# ──────────────────────────────────────────────
# Озвучка через Google TTS (работает в Streamlit)
# ──────────────────────────────────────────────
def speak(text: str):
    """Озвучивает текст через встроенный HTML-audio Streamlit."""
    try:
        from gtts import gTTS
        import io
        tts = gTTS(text=text, lang="ru")
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        st.audio(buf, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.warning(f"Ошибка озвучки: {e}")


# ──────────────────────────────────────────────
# Распознавание голоса через Whisper (локально)
# ──────────────────────────────────────────────
def transcribe_audio(audio_bytes: bytes) -> str | None:
    """Конвертирует аудио-байты в текст через OpenAI Whisper."""
    try:
        import openai, io
        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        buf = io.BytesIO(audio_bytes)
        buf.name = "voice.wav"
        result = client.audio.transcriptions.create(model="whisper-1", file=buf)
        return result.text
    except Exception as e:
        st.error(f"Ошибка распознавания голоса: {e}")
        return None


# ──────────────────────────────────────────────
# Конфигурация страницы
# ──────────────────────────────────────────────
st.set_page_config(page_title="Regalmance XT Core", layout="wide")
st.title("🚀 Regalmance XT: Full Autonomous Control (v3.5)")

# ──────────────────────────────────────────────
# Боковая панель управления
# ──────────────────────────────────────────────
st.sidebar.title("🛠 Контроль системы")

if "smart_search" not in st.session_state:
    st.session_state.smart_search = False
if "web_access" not in st.session_state:
    st.session_state.web_access = False

st.session_state.smart_search = st.sidebar.toggle(
    "🔐 Интеллектуальный поиск", value=st.session_state.smart_search
)
st.session_state.web_access = st.sidebar.toggle(
    "🌐 Доступ в Интернет", value=st.session_state.web_access
)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"SmartSearch: {'✅' if st.session_state.smart_search else '❌'}  \n"
    f"WebAccess: {'✅' if st.session_state.web_access else '❌'}"
)

# ──────────────────────────────────────────────
# Инициализация движка (один раз за сессию)
# ──────────────────────────────────────────────
if "brain" not in st.session_state:
    try:
        creds_info = json.loads(st.secrets["GOOGLE_DRIVE_KEY"])
        drive = DriveManager(creds_info)
        st.session_state.brain = StudioBrain(st.secrets["GEMINI_API_KEY"], drive)
        st.sidebar.success("Движок инициализирован ✅")
    except Exception as e:
        st.sidebar.error(f"Ошибка инициализации: {e}")
        st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

# ──────────────────────────────────────────────
# Вывод истории чата
# ──────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ──────────────────────────────────────────────
# Ввод: голос + текст
# ──────────────────────────────────────────────
st.markdown("#### 🎙 Голосовой ввод")
audio_bytes = audio_recorder(
    text="Нажмите для записи",
    recording_color="#e87070",
    neutral_color="#6aa36f",
    icon_size="2x",
)

input_text = None

# Приоритет: сначала голос (если записан), потом текст
if audio_bytes and len(audio_bytes) > 1000:  # фильтр пустых записей
    with st.spinner("Распознаю голос..."):
        transcribed = transcribe_audio(audio_bytes)
    if transcribed:
        st.info(f"🎤 Распознано: *{transcribed}*")
        input_text = transcribed

text_input = st.chat_input("Или введите команду...")
if text_input:
    input_text = text_input

# ──────────────────────────────────────────────
# Обработка запроса
# ──────────────────────────────────────────────
if input_text:
    st.session_state.messages.append({"role": "user", "content": input_text})
    with st.chat_message("user"):
        st.write(input_text)

    with st.chat_message("assistant"):
        with st.spinner("Regalmance XT думает..."):
            try:
                chat = st.session_state.brain.get_chat(
                    st.session_state.smart_search,
                    st.session_state.web_access
                )
                response = chat.send_message(input_text)
                answer = response.text
                st.write(answer)
                speak(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Ошибка ответа: {e}")

