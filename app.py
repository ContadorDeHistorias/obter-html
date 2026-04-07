import streamlit as st
import requests
from io import BytesIO
import zipfile
from urllib.parse import urlparse
import re
import time
import random

st.set_page_config(page_title="Baixar HTML", layout="centered")
st.title("📥 Baixar HTML de sites")

# Headers que simulam um navegador real
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

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

def human_delay(min_sec=2, max_sec=5):
    """Delay aleatório para simular comportamento humano."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay

# Input
links_text = st.text_area("Digite até 10 URLs, uma por linha:", height=150,                           placeholder="https://exemplo.com/pagina\nhttps://outro-site.org/artigo")
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

    # Configurações de comportamento humano
    st.info("⏱️ Simulando navegação humana com delays aleatórios...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    session = requests.Session()
    
    zip_buffer = BytesIO()
    success_count = 0
    failed_links = []
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, link in enumerate(valid_links):
            status_text.text(f"⌛ Aguardando {i+1}/{len(valid_links)}...")
            
            # Delay antes de cada requisição (comportamento humano)
            if i > 0:  # Não delay na primeira
                delay = human_delay(3, 7)
                status_text.text(f"😴 Aguardando {delay:.1f}s antes de continuar...")
            
            status_text.text(f"📥 Baixando {i+1}/{len(valid_links)}: {link[:50]}...")
            
            try:
                # Adiciona headers realistas
                headers = HEADERS.copy()
                if i > 0:
                    headers["Referer"] = valid_links[i-1]  # Simula navegação sequencial
                
                # Faz a requisição com timeout generoso
                resp = session.get(
                    link, 
                    timeout=30,                     headers=headers,
                    allow_redirects=True
                )
                resp.raise_for_status()
                
                # Detecta encoding corretamente
                if not resp.encoding or resp.encoding.lower() in ('iso-8859-1', 'latin-1'):
                    resp.encoding = resp.apparent_encoding or 'utf-8'
                
                # Verifica se é HTML
                content_type = resp.headers.get('Content-Type', '').lower()
                if 'text/html' not in content_type:
                    st.warning(f"⚠️ {link} não é HTML ({content_type})")
                
                filename = safe_filename(link)
                zip_file.writestr(filename, resp.text)
                success_count += 1
                
                # Delay após sucesso
                human_delay(1, 3)
                
            except requests.exceptions.Timeout:
                error_msg = f"⏱ Timeout em {link}"
                st.error(error_msg)
                failed_links.append((link, "Timeout"))
            except requests.exceptions.TooManyRedirects:
                error_msg = f"🔄 Redirecionamentos demais em {link}"
                st.error(error_msg)
                failed_links.append((link, "Muitos redirecionamentos"))
            except requests.exceptions.RequestException as e:
                error_msg = f"❌ Erro em {link}: {type(e).__name__}"
                st.error(error_msg)
                failed_links.append((link, str(e)))
            
            progress_bar.progress((i + 1) / len(valid_links))
    
    status_text.empty()
    progress_bar.empty()
    
    # Resumo dos resultados
    if failed_links:
        with st.expander(f"❌ {len(failed_links)} falhas"):
            for link, error in failed_links:
                st.write(f"**{link}**: {error}")
    
    if success_count > 0:
        zip_buffer.seek(0)
        st.success(f"✅ {success_count}/{len(valid_links)} páginas baixadas com sucesso!")
        
        if success_count < len(valid_links):            st.warning(f"⚠️ {len(valid_links) - success_count} falharam, mas o ZIP contém as bem-sucedidas")
        
        st.download_button(
            label="📦 Baixar ZIP",
            data=zip_buffer,
            file_name="sites_html.zip",
            mime="application/zip",
            disabled=success_count == 0
        )
    else:
        st.error("❌ Nenhuma página foi baixada. Verifique os erros acima.")
    
    st.info("💡 Dica: Sites com proteção anti-bot podem ainda bloquear. Tente novamente mais tarde se necessário.")
