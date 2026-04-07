import streamlit as st
import requests
from io import BytesIO
import zipfile
from urllib.parse import urlparse
import re
import time
import random
import gzip
import brotli
import zlib

st.set_page_config(page_title="Baixar HTML", layout="centered")
st.title("📥 Baixar HTML de sites")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def decompress_content(response):
    """Descomprime conteúdo se necessário."""
    content = response.content
    encoding = response.headers.get('Content-Encoding', '').lower()
    
    try:
        if 'gzip' in encoding:
            content = gzip.decompress(content)
        elif 'br' in encoding:
            content = brotli.decompress(content)
        elif 'deflate' in encoding:
            content = zlib.decompress(content)
    except Exception as e:
        st.warning(f"Aviso: Erro ao descomprimir: {e}")
    
    return content

def get_html_text(response):
    """Extrai texto HTML corretamente."""
    content = decompress_content(response)
    encoding = response.apparent_encoding or 'utf-8'
    
    try:
        html_text = content.decode(encoding, errors='replace')
    except Exception:
        html_text = content.decode('utf-8', errors='replace')    
    return html_text

def safe_filename(url: str) -> str:
    """Gera nome de arquivo seguro."""
    parsed = urlparse(url)
    name = parsed.netloc + parsed.path
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    return (name.strip('_') or 'page') + '.html'

def is_valid_url(url: str) -> bool:
    """Valida URL."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False

def human_delay(min_sec=2, max_sec=5):
    """Delay aleatório."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay

# Input
links_text = st.text_area("Digite até 10 URLs, uma por linha:", height=150)
links = [link.strip() for link in links_text.split('\n') if link.strip()]

if len(links) > 10:
    st.error("⚠️ Limite de 10 links.")
    st.stop()

if st.button("🔽 Baixar HTML", disabled=not links):
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
                delay = human_delay(3, 7)                status_text.text(f"😴 Aguardando {delay:.1f}s...")
            
            status_text.text(f"📥 {i+1}/{len(valid_links)}: {link[:50]}...")
            
            try:
                headers = HEADERS.copy()
                if i > 0:
                    headers["Referer"] = valid_links[i-1]
                
                resp = session.get(link, timeout=30, headers=headers, allow_redirects=True)
                resp.raise_for_status()
                
                content_type = resp.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                    st.warning(f"⚠️ {link[:50]}... não é HTML")
                    continue
                
                html_text = get_html_text(resp)
                
                if not html_text.strip().startswith(('<!DOCTYPE', '<html', '<HTML')):
                    st.warning(f"⚠️ {link[:50]}... conteúdo inválido")
                    continue
                
                filename = safe_filename(link)
                zip_file.writestr(filename, html_text.encode('utf-8'))
                success_count += 1
                
                human_delay(1, 3)
                
            except Exception as e:
                st.error(f"❌ Erro em {link[:50]}...: {type(e).__name__}")
            
            progress_bar.progress((i + 1) / len(valid_links))
    
    status_text.empty()
    progress_bar.empty()
    
    if success_count > 0:
        zip_buffer.seek(0)
        st.success(f"✅ {success_count}/{len(valid_links)} páginas baixadas!")
        st.download_button(
            label="📦 Baixar ZIP",
            data=zip_buffer,
            file_name="sites_html.zip",
            mime="application/zip"
        )
    else:
        st.error("❌ Nenhuma página válida baixada.")
