import streamlit as st
import requests

st.title("Obter HTML de um site")

# Input da URL
url = st.text_input("Digite a URL do site:")

if st.button("Obter HTML"):
    if url:
        try:
            resposta = requests.get(url, timeout=10)
            resposta.raise_for_status()
            st.code(resposta.text, language='html')
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao acessar o site: {e}")
    else:
        st.warning("Digite uma URL válida!")
