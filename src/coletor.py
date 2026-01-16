import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from pypdf import PdfReader
from io import BytesIO
import json
import os
from datetime import datetime
import pytz
import urllib3
from urllib.parse import unquote

# --- CONFIGURAÇÃO DE CAMINHOS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(root_dir, 'data', 'dados.json')
STATUS_FILE = os.path.join(root_dir, 'data', 'status.json') # Novo arquivo de status

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TARGET_URL = "https://diof.ro.gov.br"
TZ_ACRE = pytz.timezone('America/Rio_Branco')

def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Monitor DIOF Bot)'})
    return session

def get_clean_filename(url):
    try: return unquote(url.split('/')[-1]).split('?')[0]
    except: return "Documento PDF"

def extract_pages_from_pdf(session, url):
    try:
        response = session.get(url, verify=False, stream=True, timeout=60)
        f = BytesIO(response.content)
        reader = PdfReader(f)
        
        pages_data = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip(): 
                pages_data.append({
                    "number": i + 1,
                    "text": text
                })
        return pages_data
    except Exception as e:
        print(f"⚠️ Erro ao ler PDF {url}: {e}")
        return []

def save_status():
    """Salva o horário da última verificação do robô"""
    status = {
        "last_run": datetime.now(TZ_ACRE).strftime("%d/%m/%Y %H:%M:%S"),
        "message": "Sistema Operante"
    }
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
        print(f"⏱️ Status atualizado: {status['last_run']}")
    except Exception as e:
        print(f"Erro ao salvar status: {e}")

def main():
    session = get_session()
    
    # Garante que a pasta existe
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try: database = json.load(f)
            except: database = []
    else:
        database = []

    processed_urls = {item['url'] for item in database}

    try:
        print(f"📡 Verificando {TARGET_URL}...")
        response = session.get(TARGET_URL, verify=False, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"❌ Erro de acesso: {e}")
        # Mesmo com erro, tentamos salvar o status para mostrar a hora da tentativa
        save_status() 
        return

    links_on_page = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.lower().endswith('.pdf') and "d29900" not in href.lower():
            full_url = href if href.startswith('http') else f"{TARGET_URL.rstrip('/')}/{href.lstrip('/')}"
            title = link.get_text(strip=True)
            if not title or title.lower() in ['baixar', 'download', 'pdf']:
                title = get_clean_filename(full_url)
            links_on_page.append({"title": title, "url": full_url})

    new_found = False
    for item in reversed(links_on_page): 
        if item['url'] not in processed_urls:
            print(f"🚨 NOVO PDF: {item['title']}")
            pages_content = extract_pages_from_pdf(session, item['url'])
            
            if pages_content:
                new_entry = {
                    "title": item['title'],
                    "url": item['url'],
                    "scraped_at": datetime.now(TZ_ACRE).strftime("%d/%m/%Y %H:%M:%S"),
                    "pages_content": pages_content
                }
                database.insert(0, new_entry)
                processed_urls.add(item['url'])
                new_found = True

    if new_found:
        database = database[:50]
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        print(f"✅ Base de dados atualizada!")
    else:
        print("zzz Sem novos PDFs.")
    
    # SALVA O STATUS (SEMPRE)
    save_status()

if __name__ == "__main__":
    main()