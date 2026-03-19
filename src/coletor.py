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

# --- NOVOS IMPORTS PARA O E-MAIL ---
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
import urllib.request

# --- CONFIGURAÇÃO DE CAMINHOS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(root_dir, 'data', 'dados.json')
STATUS_FILE = os.path.join(root_dir, 'data', 'status.json')

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

# --- NOVA FUNÇÃO: VERIFICAR E ENVIAR ALERTAS ---
def verificar_e_enviar_alertas(texto_do_pdf_novo, titulo_pdf, link_pdf):
    LINK_PLANILHA_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTHg_b0ffTU4kup8hZkmXW4SFWPazoqYT0bt4PHlsnyBn5wO_82pb7bvuTY7YYwX3_k1RFWFHR4wYYz/pub?output=csv"
    
    gmail_user = os.environ.get('GMAIL_USER')
    gmail_password = os.environ.get('GMAIL_PASSWORD')

    if not gmail_user or not gmail_password:
        print("⚠️ Credenciais de e-mail (GMAIL_USER ou GMAIL_PASSWORD) não configuradas no GitHub Secrets.")
        return

    try:
        # Baixa os dados da planilha
        resposta = urllib.request.urlopen(LINK_PLANILHA_CSV)
        linhas = [l.decode('utf-8') for l in resposta.readlines()]
        leitor_csv = csv.reader(linhas)
        
        cabecalho = next(leitor_csv, None) 
        
        usuarios_ativos = {}
        
        # Lê a planilha de cima para baixo. E-mails repetidos vão sobrescrever e manter só a resposta mais recente.
        for linha in leitor_csv:
            if len(linha) >= 6: 
                nome = linha[1].strip()
                email_usuario = linha[2].strip().lower()
                termo = linha[5].strip()
                
                if email_usuario and termo:
                    usuarios_ativos[email_usuario] = {
                        'nome': nome,
                        'termo': termo
                    }
        
        if not usuarios_ativos:
            print("Nenhum usuário cadastrado para alertas.")
            return

        # Verifica quem vai receber e-mail
        emails_para_enviar = []
        for email, dados in usuarios_ativos.items():
            termo_busca = dados['termo'].lower()
            if termo_busca in texto_do_pdf_novo.lower():
                emails_para_enviar.append((email, dados['nome'], dados['termo']))

        # Dispara os e-mails
        if emails_para_enviar:
            print(f"🔔 Encontramos {len(emails_para_enviar)} alertas para enviar!")
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, gmail_password)
            
            for email_destino, nome, termo in emails_para_enviar:
                msg = MIMEMultipart()
                msg['From'] = gmail_user
                msg['To'] = email_destino
                msg['Subject'] = f"🚨 Alerta DIOF-RO: Encontramos o termo '{termo}'"
                
                corpo_email = f"""Olá {nome},
                
Temos uma excelente notícia! O sistema do BT System acabou de encontrar uma correspondência para você.

O termo "{termo}" que você cadastrou apareceu em uma nova edição do Diário Oficial de Rondônia.

📄 Documento: {titulo_pdf}
🔗 Link para acesso: {link_pdf}

Dica: Ao abrir o PDF, aperte CTRL+F (ou busque na página no celular) e digite o seu termo para achá-lo rapidamente dentro do documento.

Para alterar o seu termo de busca atual, basta preencher nosso formulário de cadastro novamente usando este mesmo e-mail.

Atenciosamente,
Robô de Alertas - BT System
"""
                msg.attach(MIMEText(corpo_email, 'plain'))
                server.send_message(msg)
                print(f"✅ E-mail enviado com sucesso para: {email_destino}")
                
            server.quit()
        else:
            print("Nenhum termo cadastrado foi encontrado neste PDF.")

    except Exception as e:
        print(f"❌ Erro ao processar ou enviar alertas: {e}")

# --- CÓDIGO PRINCIPAL ---
def main():
    session = get_session()
    
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
            
            # 1. Extrai o conteúdo em PDF
            pages_content = extract_pages_from_pdf(session, item['url'])
            
            if pages_content:
                # 2. Salva no banco de dados
                new_entry = {
                    "title": item['title'],
                    "url": item['url'],
                    "scraped_at": datetime.now(TZ_ACRE).strftime("%d/%m/%Y %H:%M:%S"),
                    "pages_content": pages_content
                }
                database.insert(0, new_entry)
                processed_urls.add(item['url'])
                new_found = True
                
                # 3. GATILHO DOS ALERTAS: Junta o texto de todas as páginas e envia pro verificador
                print(f"🔍 Verificando se há alertas configurados para {item['title']}...")
                texto_completo = " ".join([page['text'] for page in pages_content])
                verificar_e_enviar_alertas(texto_completo, item['title'], item['url'])

    if new_found:
        database = database[:50]
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)
        print(f"✅ Base de dados atualizada!")
    else:
        print("zzz Sem novos PDFs.")
    
    save_status()

if __name__ == "__main__":
    main()