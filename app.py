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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
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

links_text = st.text_area("Digite até 10 URLs, uma por linha:", height=150)
links = [link.strip() for link in links_text.split('\n') if link.strip()]

if len(links) > 10:
    st.error("Limite de 10 links.")
    st.stop()

if st.button("Baixar HTML", disabled=not links):
    valid_links = [l for l in links if is_valid_url(l)]
    
    if not valid_links:
        st.error("Nenhuma URL valida.")
        st.stop()

    st.info(f"Processando {len(valid_links)} URL(s)...")
        progress_bar = st.progress(0)
    status_text = st.empty()
    results = []
    session = requests.Session()
    zip_buffer = BytesIO()
    success_count = 0

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, link in enumerate(valid_links):
            if i > 0:
                delay = random.uniform(3, 7)
                status_text.text(f"Aguardando {delay:.1f}s...")
                time.sleep(delay)
            
            status_text.text(f"Baixando {i+1}/{len(valid_links)}: {link[:50]}...")
            
            try:
                headers = HEADERS.copy()
                resp = session.get(link, timeout=30, headers=headers, allow_redirects=True)
                
                status = f"Status: {resp.status_code}"
                content_type = resp.headers.get('Content-Type', 'Unknown')
                
                if resp.status_code == 200 and 'text/html' in content_type.lower():
                    html_content = resp.text
                    filename = safe_filename(link)
                    zip_file.writestr(filename, html_content.encode('utf-8', errors='replace'))
                    success_count += 1
                    results.append(f"✅ {link[:50]}... ({len(html_content)} bytes)")
                else:
                    results.append(f"❌ {link[:50]}... (Status: {resp.status_code}, Tipo: {content_type})")
                    st.warning(f"URL ignorada: {link[:50]}... - Status {resp.status_code}")
                    
            except Exception as e:
                results.append(f"❌ {link[:50]}... (Erro: {type(e).__name__})")
                st.error(f"Erro: {link[:50]}... - {type(e).__name__}: {str(e)[:100]}")
            
            progress_bar.progress((i + 1) / len(valid_links))

    status_text.empty()
    progress_bar.empty()
    
    # Mostra resultados detalhados
    if results:
        with st.expander(f"Ver detalhes ({len(results)} URLs)"):
            for r in results:
                st.write(r)
    
    st.write(f"**Sucesso:** {success_count}/{len(valid_links)}")
        if success_count > 0:
        zip_buffer.seek(0)
        st.success(f"{success_count}/{len(valid_links)} paginas baixadas!")
        
        # Debug: mostra tamanho do ZIP
        zip_size = zip_buffer.tell()
        st.info(f"Tamanho do ZIP: {zip_size} bytes")
        
        st.download_button(
            label="📦 Baixar ZIP",
            data=zip_buffer.getvalue(),
            file_name="sites_html.zip",
            mime="application/zip",
            use_container_width=True
        )
    else:
        st.error("Nenhuma pagina baixada. Verifique os erros acima.")
        st.info("Dica: Alguns sites bloqueiam requisições automatizadas. Tente sites como wikipedia.org")
