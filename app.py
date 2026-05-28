import streamlit as st
import google.generativeai as genai
import os

# 1. НАСТРОЙКА API
api_key = st.secrets.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

st.set_page_config(page_title="Obsidian Essence Debug", layout="centered")
st.title("Диагностика Мозга Студии")

# 2. БЛОК ДИАГНОСТИКИ (вывод доступных моделей в логи и на экран)
st.subheader("Список доступных моделей:")
try:
    models = genai.list_models()
    model_names = [m.name for m in models]
    st.write(model_names) # Вывод моделей на экран для наглядности
    
    # Автоматический выбор модели (если 2.5 есть, берем её, если нет - 1.5)
    selected_model = "gemini-2.5-pro" if "models/gemini-2.5-pro" in model_names else "gemini-1.5-pro"
    st.info(f"Система выбрала для работы: {selected_model}")
    
    model = genai.GenerativeModel(selected_model)
except Exception as e:
    st.error(f"Ошибка при получении списка моделей: {e}")
    st.stop()

# 3. ЧАТ-БОТ
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Введите задачу..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        try:
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Ошибка API: {e}")


