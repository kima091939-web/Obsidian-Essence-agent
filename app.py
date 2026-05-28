import streamlit as st
import google.generativeai as genai

# Заголовок приложения
st.title("Obsidian Essence Agent")

# Получение ключа из настроек Streamlit (Secrets)
api_key = st.secrets.get("GOOGLE_API_KEY")

if not api_key:
    st.error("API-ключ не найден. Добавьте его в настройки Streamlit.")
else:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    # Интерфейс чата
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Что спросим у Obsidian?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = model.generate_content(prompt)
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

