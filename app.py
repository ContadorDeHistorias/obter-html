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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}

def safe_filename(url):
    parsed = urlparse(url)
    name = parsed.netloc + parsed.path
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    return (name.strip('_') or 'page') + '.html'

def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False

def human_delay(min_sec, max_sec):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay

links_text = st.text_area("Digite até 10 URLs, uma por linha:", height=150)
links = [link.strip() for link in links_text.split('\n') if link.strip()]

if len(links) > 10:
    st.error("Limite de 10 links.")
    st.stop()

if st.button("Baixar HTML", disabled=not links):
    valid_links = [l for l in links if is_valid_url(l)]
    
    if not valid_links:
        st.error("Nenhuma URL válida.")
        st.stop()
    progress_bar = st.progress(0)
    status_text = st.empty()
    session = requests.Session()
    zip_buffer = BytesIO()
    success_count = 0
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, link in enumerate(valid_links):
            if i > 0:
                delay = human_delay(3, 7)
                status_text.text(f"Aguardando {delay:.1f}s...")
            
            status_text.text(f"{i+1}/{len(valid_links)}: {link[:50]}...")
            
            try:
                headers = HEADERS.copy()
                if i > 0:
                    headers["Referer"] = valid_links[i-1]
                
                resp = session.get(link, timeout=30, headers=headers, allow_redirects=True)
                resp.raise_for_status()
                
                content_type = resp.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type:
                    st.warning(f"Nao e HTML: {link[:50]}...")
                    continue
                
                html_text = resp.text
                
                if not html_text.strip().startswith('<'):
                    st.warning(f"Conteudo invalido: {link[:50]}...")
                    continue
                
                filename = safe_filename(link)
                zip_file.writestr(filename, html_text.encode('utf-8'))
                success_count += 1
                
                human_delay(1, 3)
                
            except Exception as e:
                st.error(f"Erro em {link[:50]}...: {type(e).__name__}")
            
            progress_bar.progress((i + 1) / len(valid_links))
    
    status_text.empty()
    progress_bar.empty()
    
    if success_count > 0:
        zip_buffer.seek(0)        st.success(f"{success_count}/{len(valid_links)} paginas baixadas!")
        st.download_button(
            label="Baixar ZIP",
            data=zip_buffer,
            file_name="sites_html.zip",
            mime="application/zip"
        )
    else:
        st.error("Nenhuma pagina valida baixada.")
