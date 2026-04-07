import streamlit as st
import requests
from io import BytesIO
import zipfile
from urllib.parse import urlparse
import re

st.set_page_config(page_title="Baixar HTML", layout="centered")
st.title("📥 Baixar HTML de sites")

def safe_filename(url: str) -> str:
    """Gera nome de arquivo seguro a partir da URL."""
    parsed = urlparse(url)
    name = parsed.netloc + parsed.path
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
    return (name.strip('_') or 'page') + '.html'

def is_valid_url(url: str) -> bool:
    """Valida esquema e estrutura básica da URL."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except:
        return False

# Input
links_text = st.text_area("Digite até 10 URLs, uma por linha:", height=150)
links = [link.strip() for link in links_text.split('\n') if link.strip()]

if len(links) > 10:
    st.error("⚠️ Limite de 10 links por vez.")
    st.stop()

if st.button("🔽 Baixar HTML", disabled=not links):
    valid_links = [l for l in links if is_valid_url(l)]
    invalid = set(links) - set(valid_links)
    
    if invalid:
        st.warning(f"URLs inválidas ignoradas: {', '.join(invalid)}")
    
    if not valid_links:
        st.error("Nenhuma URL válida para processar.")
        st.stop()

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    zip_buffer = BytesIO()
    success_count = 0
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, link in enumerate(valid_links):
            status_text.text(f"Processando {i+1}/{len(valid_links)}: {link[:50]}...")
            try:
                resp = requests.get(link, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                resp.raise_for_status()
                # Detecta encoding corretamente
                if not resp.encoding or resp.encoding.lower() == 'iso-8859-1':
                    resp.encoding = resp.apparent_encoding or 'utf-8'
                
                filename = safe_filename(link)
                zip_file.writestr(filename, resp.text)
                success_count += 1
                
            except requests.exceptions.Timeout:
                st.error(f"⏱ Timeout em {link}")
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Erro em {link}: {type(e).__name__}")
            
            progress_bar.progress((i + 1) / len(valid_links))
    
    status_text.empty()
    progress_bar.empty()
    
    # Só mostra download se houve sucesso
    if success_count > 0:
        zip_buffer.seek(0)
        st.success(f"✅ {success_count}/{len(valid_links)} páginas baixadas!")
        st.download_button(
            label="📦 Baixar ZIP",
            data=zip_buffer,
            file_name="sites_html.zip",
            mime="application/zip",
            disabled=success_count == 0
        )
    else:
        st.error("Nenhum HTML foi baixado. Verifique os erros acima.")
