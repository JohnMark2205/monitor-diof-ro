import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from pypdf import PdfReader
from io import BytesIO
import json
import os
from datetime import datetime
import pytz # Biblioteca para fuso horário
import urllib3
from urllib.parse import unquote

# 1. Configuração Robusta
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
DB_FILE = "dados.json"
TARGET_URL = "https://diof.ro.gov.br"

# Configura Fuso do Acre
TZ_ACRE = pytz.timezone('America/Rio_Branco')

def get_session():
    """Cria uma sessão com estratégia de retentativa (Retry)"""
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

def extract_text_from_pdf(session, url):
    """Baixa o PDF e extrai texto com tratamento de erro"""
    try:
        response = session.get(url, verify=False, stream=True, timeout=60)
        f = BytesIO(response.content)
        reader = PdfReader(f)
        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text
    except Exception as e:
        print(f"⚠️ Erro ao ler PDF {url}: {e}")
        return None

def main():
    session = get_session()
    
    # 1. Carregar base existente
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try: database = json.load(f)
            except: database = []
    else:
        database = []

    # Cria índice de URLs já processadas para checagem rápida (O(1))
    processed_urls = {item['url'] for item in database}

    # 2. Acessar Site
    try:
        print(f"📡 Verificando atualizações em {TARGET_URL}...")
        response = session.get(TARGET_URL, verify=False, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"❌ Falha crítica ao acessar o site: {e}")
        return # Encerra sem quebrar o fluxo do GitHub Actions

    # 3. Filtrar Links
    new_found = False
    
    # Pega todos os links da home
    links_on_page = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.lower().endswith('.pdf') and "d29900" not in href.lower():
            full_url = href if href.startswith('http') else f"{TARGET_URL.rstrip('/')}/{href.lstrip('/')}"
            title = link.get_text(strip=True)
            if not title or title.lower() in ['baixar', 'download', 'pdf']:
                title = get_clean_filename(full_url)
            
            # Adiciona na lista para verificar
            links_on_page.append({"title": title, "url": full_url})

    # 4. Processar Novos
    # A mágica acontece aqui: invertemos a lista para processar do mais antigo pro mais novo na página,
    # mas inserimos no topo do banco de dados.
    for item in reversed(links_on_page): 
        if item['url'] not in processed_urls:
            print(f"🚨 NOVO PDF DETECTADO: {item['title']}")
            print(f"   ⬇️ Baixando e indexando conteúdo...")
            
            content = extract_text_from_pdf(session, item['url'])
            
            if content:
                # Cria registro com data do Acre
                now_acre = datetime.now(TZ_ACRE).strftime("%d/%m/%Y %H:%M:%S")
                
                new_entry = {
                    "title": item['title'],
                    "url": item['url'],
                    "scraped_at": now_acre,
                    "content": content
                }
                
                # Insere no INÍCIO da lista (posição 0) para aparecer primeiro na busca
                database.insert(0, new_entry)
                processed_urls.add(item['url']) # Marca como processado
                new_found = True
        else:
            # Se já existe, ignoramos silenciosamente para economizar log
            pass

    # 5. Salvar apenas se houve mudança
    if new_found:
        # Limita o histórico para não estourar o limite do GitHub (ex: últimos 100 diários)
        database = database[:100]
        
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        print(f"✅ Banco de dados atualizado com sucesso! Novos registros inseridos.")
    else:
        print("zzz Nenhuma alteração encontrada no site nesta hora.")

if __name__ == "__main__":
    main()