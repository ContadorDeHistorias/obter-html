import streamlit as st
import requests
from io import BytesIO
import zipfile

st.title("Baixar HTML de sites")

# Input dos links
links_text = st.text_area("Digite até 10 URLs, uma por linha:")
links = [link.strip() for link in links_text.split('\n') if link.strip()]

if len(links) > 10:
    st.warning("Limite de 10 links por vez.")

if st.button("Baixar HTML") and links and len(links) <= 10:
    # Criar um arquivo zip em memória
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for link in links:
            try:
                resposta = requests.get(link, timeout=10)
                resposta.raise_for_status()
                filename = link.replace('https://', '').replace('http://', '').replace('/', '_') + '.html'
                zip_file.writestr(filename, resposta.text)
            except requests.exceptions.RequestException as e:
                st.error(f"Erro ao acessar {link}: {e}")

    zip_buffer.seek(0)
    st.download_button(
        label="Baixar todos os HTMLs como ZIP",
        data=zip_buffer,
        file_name="sites_html.zip",
        mime="application/zip"
    )
