import streamlit as st
import requests
from io import BytesIO
import zipfile
from urllib.parse import urlparse
import re
import time
import random

st.set_page_config(page_title="Baixar HTML", layout="centered")
st.title("Baixar HTML de sites")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html",
    "Accept-Language": "pt-BR",
}

def safe_filename(url):
    parsed = urlparse(url)
    name = parsed.netloc + parsed.path
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    return (name.strip('_') or 'page') + '.html'

def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False

links_text = st.text_area(" URLs, uma por linha:", height=150)
links = [link.strip() for link in links_text.split('\n') if link.strip()]

if len(links) > 10:
    st.error("Limite de 10 links.")
    st.stop()

if st.button("Baixar HTML", disabled=not links):
    valid_links = [l for l in links if is_valid_url(l)]
    if not valid_links:
        st.error("Nenhuma URL valida.")
        st.stop()

    progress_bar = st.progress(0)
    session = requests.Session()
    zip_buffer = BytesIO()
    success_count = 0

    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for i, link in enumerate(valid_links):
            if i > 0:
                time.sleep(random.uniform(3, 7))
            try:
                resp = session.get(link, timeout=30, headers=HEADERS)
                resp.raise_for_status()
                if 'text/html' in resp.headers.get('Content-Type', ''):
                    filename = safe_filename(link)
                    zip_file.writestr(filename, resp.text.encode('utf-8'))
                    success_count += 1
            except Exception as e:
                st.error(f"Erro: {link[:40]}... - {type(e).__name__}")
            progress_bar.progress((i + 1) / len(valid_links))

    progress_bar.empty()
    if success_count > 0:
        zip_buffer.seek(0)
        st.success(f"{success_count}/{len(valid_links)} paginas baixadas!")
        st.download_button(
            label="Baixar ZIP",
            data=zip_buffer,
            file_name="sites_html.zip",
            mime="application/zip"
        )
    else:
        st.error("Nenhuma pagina baixada.")