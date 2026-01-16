import streamlit as st
import json
import os
import base64
from datetime import datetime
import requests
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Monitor DIOF-RO", 
    page_icon="⚖️", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CONFIGURAÇÃO DE CAMINHOS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(root_dir, 'data', 'dados.json')
STATUS_FILE = os.path.join(root_dir, 'data', 'status.json')
LOGO_PATH = os.path.join(root_dir, 'assets', 'logo_diof.png')

# --- LINK DO FORMULÁRIO DE CONTATO ---
CONTACT_FORM_URL = "https://forms.google.com/seu-formulario-aqui" 

# --- CSS VISUAL ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 8rem; }
    
    /* --- CORREÇÃO DEFINITIVA DA LOGO (V15) --- */
    .logo-container-final {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-bottom: 10px;
        padding: 0 10px; /* Margem de segurança nas laterais */
    }

    .logo-img-final {
        /* REGRA DE OURO: Controlar pela altura para não ficar gigante */
        height: auto; 
        max-height: 80px; /* Altura máxima permitida (evita ficar enorme) */
        
        /* Segurança para Mobile */
        width: auto;
        max-width: 100%; /* Nunca ultrapassa a largura da tela */
        
        object-fit: contain; /* Garante que nunca corte */
    }
    /* --- FIM DA CORREÇÃO --- */

    
    /* INPUTS (Dark Mode Friendly) */
    div[data-baseweb="input"] {
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border: 2px solid #2563eb !important;
        box-shadow: none !important;
    }
    .stTextInput input {
        color: #ffffff !important;
        caret-color: #2563eb !important;
    }
    
    /* BOTÕES */
    .stButton button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        height: 48px;
        font-weight: 600 !important;
        border: none !important;
        width: 100%;
        transition: background 0.3s;
        margin-top: 1px;
    }
    .stButton button:hover { background-color: #1d4ed8 !important; }

    /* CARDS DE RESULTADO */
    .result-card {
        background-color: rgba(37, 99, 235, 0.05); 
        border: 1px solid rgba(37, 99, 235, 0.2);
        padding: 16px; 
        border-radius: 12px; 
        margin-bottom: 16px; 
        border-left: 5px solid #2563eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .snippet-box {
        background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; 
        font-family: monospace; font-size: 0.85rem; margin: 12px 0;
        color: #e5e7eb; border: 1px solid rgba(255,255,255,0.05); line-height: 1.4;
    }
    .pdf-button {
        display: block; width: 100%; background-color: #2563eb; color: white !important;
        text-decoration: none !important; padding: 12px 0; border-radius: 8px;
        font-weight: 600; text-align: center; margin-top: 15px; border: none;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); transition: all 0.2s ease-in-out;
    }
    .pdf-button:hover {
        background-color: #1d4ed8; transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(37, 99, 235, 0.3);
    }
    .streamlit-expanderHeader {
        font-size: 0.9rem; font-weight: 600; color: #2563eb;
        background-color: rgba(37, 99, 235, 0.05); border-radius: 8px;
    }
    
    /* TEXTOS DE STATUS */
    .status-highlight {
        color: #34d399; /* Verde Suave */
        font-weight: 600;
    }
    
    /* FOOTER */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: rgba(14, 17, 23, 0.98); color: #9ca3af; text-align: center;
        padding: 15px 20px; z-index: 99999; border-top: 1px solid rgba(255,255,255,0.1);
        display: flex; flex-direction: column; gap: 5px; backdrop-filter: blur(5px);
    }
    .footer-credits { font-size: 0.85rem; font-weight: 600; color: #d1d5db; }
    .footer-disclaimer { font-size: 0.7rem; opacity: 0.8; line-height: 1.3; }
    
    @media (prefers-color-scheme: light) {
        .result-card { background-color: #f0f9ff; border: 1px solid #bae6fd; }
        .snippet-box { background: #f1f5f9; color: #374151; border: 1px solid #e2e8f0; }
        .footer { background-color: rgba(255, 255, 255, 0.98); color: #4b5563; border-top: 1px solid #e5e7eb; }
        .footer-credits { color: #1f2937; }
        .stTextInput input { color: #1e293b !important; } 
        div[data-baseweb="input"] { border: 1px solid #cbd5e1 !important; }
        .status-highlight { color: #059669; }
    }
    </style>
""", unsafe_allow_html=True)

# --- FUNÇÕES ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def load_data():
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except: return []

def load_status():
    if not os.path.exists(STATUS_FILE): return None
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return None

def search_local(term, data):
    results = []
    term_lower = term.lower()
    for doc in data:
        found_pages = []
        full_text_found = "" 
        snippet = ""
        try:
            pages = doc.get('pages_content', [])
            for page in pages:
                if term_lower in page['text'].lower():
                    page_num = str(page['number']).strip()
                    found_pages.append(page_num)
                    if not full_text_found: full_text_found = page['text']
                    if not snippet:
                        idx = page['text'].lower().find(term_lower)
                        start = max(0, idx - 40)
                        end = min(len(page['text']), idx + 100)
                        snippet = page['text'][start:end].replace("\n", " ")
            if not found_pages and 'content' in doc:
                 if term_lower in doc['content'].lower():
                    found_pages.append("9999") 
                    idx = doc['content'].lower().find(term_lower)
                    snippet = doc['content'][idx:idx+100]
        except: continue
        if found_pages:
            unique_pages = sorted(list(set(found_pages)), key=lambda x: int(x) if x.isdigit() else 9999)
            results.append({
                "title": doc['title'],
                "url": doc['url'],
                "date": doc.get('scraped_at', 'Data desc.'),
                "pages": unique_pages,
                "snippet": snippet,
                "full_text": full_text_found
            })
    return results

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    st.info("O sistema verifica novas edições automaticamente a cada 30 minutos.")
    st.divider()
    st.write("**Precisa de ajuda?**")
    st.write("Não encontrou o que buscava ou notou algum erro na aplicação?")
    st.link_button("📧 Entrar em Contato", url=CONTACT_FORM_URL, use_container_width=True)

# --- HEADER (LOGOTIPO AJUSTADO) ---
img_b64 = get_base64_image(LOGO_PATH)
if img_b64:
    st.markdown(f"""
        <div class="logo-container-final">
            <img src="data:image/png;base64,{img_b64}" class="logo-img-final">
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""<div style='text-align: center; margin-bottom: 20px;'><h1 style='color:#0068c9;'>BT</h1></div>""", unsafe_allow_html=True)


# --- TÍTULO E STATUS ---
data = load_data()
status = load_status()

display_date = "Desconhecido"
if status and 'last_run' in status:
    display_date = status['last_run']
elif data:
    display_date = data[0].get('scraped_at', 'Desconhecido')

st.markdown(f"""
<div style="text-align:center; margin-top:-10px;">
    <h1 style="font-weight:800; font-size:1.8rem; margin:0;">Buscador de Termos</h1>
    <p style="font-size:0.9rem; opacity:0.7; margin-top:5px; margin-bottom:5px;">Monitoramento Automatizado</p>
    <p style="font-size:0.8rem; font-family:monospace; color:#9ca3af;">
        ✅ Última verificação: <span class="status-highlight">{display_date}</span>
    </p>
</div>
""", unsafe_allow_html=True)

# --- INFO DE ESCOPO ---
if data:
    st.info(f"""
    📂 **Escopo da Pesquisa:** O sistema monitora as **{len(data)} edições mais recentes** disponíveis na capa do portal DIOF.
    \n*⚠️ Atenção: Não realizamos buscas no acervo histórico completo (anos anteriores), apenas nas edições vigentes do painel.*
    """)
else:
    st.warning("⚠️ Base de dados vazia. Aguardando primeira execução.")

# --- FORM DE BUSCA ---
st.write("O que você procura?")
with st.form(key='search_form'):
    col1, col2 = st.columns([4, 1], gap="small")
    with col1:
        query = st.text_input(label="Busca", placeholder="Digite Nome, CPF, Matrícula...", label_visibility="collapsed")
    with col2:
        submit_button = st.form_submit_button(label="🔍 Pesquisar")

if submit_button or query:
    if not query:
        st.warning("⚠️ Digite algo para pesquisar.")
    elif not data:
        st.error("Sem dados para pesquisar.")
    else:
        start_time = datetime.now()
        results = search_local(query, data)
        duration = (datetime.now() - start_time).total_seconds()
        
        if results:
            st.success(f"🔍 Encontrado em {len(results)} documentos ({duration:.3f}s)")
            for res in results:
                base_url = res['url'].strip()
                if "?" in base_url: base_url = base_url.split("?")[0]
                first_page = res['pages'][0] if res['pages'] else None
                
                if first_page and first_page != "9999" and first_page.isdigit():
                    pdf_link = f"{base_url}#page={first_page}"
                    btn_text = f"Abrir PDF na Pág. {first_page}"
                else:
                    pdf_link = base_url
                    btn_text = "Abrir PDF Original"

                if "9999" in res['pages']: pages_display = "Localizado no texto (Base antiga)"
                else:
                    pages_str = ', '.join(res['pages'])
                    if len(res['pages']) > 15: pages_str = f"{', '.join(res['pages'][:15])}..."
                    pages_display = f"Página(s): <strong>{pages_str}</strong>"

                html_card = f"""
<div class="result-card">
    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
        <h3 style="margin:0; font-size:1.1rem; color:#2563eb; line-height:1.2;">📄 {res['title']}</h3>
        <span style="font-size:0.75rem; color:#6b7280; white-space:nowrap; margin-left:10px;">{res['date']}</span>
    </div>
    <p style="margin:12px 0 8px 0; font-size:0.95rem;">
        ✅ {pages_display}
    </p>
    <div class="snippet-box">
        ...{res['snippet']}...
    </div>
    <a href="{pdf_link}" target="_blank" class="pdf-button">
        {btn_text}
    </a>
</div>
"""
                st.markdown(html_card, unsafe_allow_html=True)
                if res.get('full_text'):
                    with st.expander(f"📱 Leitura Rápida (Pág. {first_page})"):
                        st.text_area("Conteúdo:", value=res['full_text'], height=300, disabled=True, label_visibility="collapsed")
                        st.caption("Texto extraído automaticamente.")
        else:
            st.warning(f"O termo **'{query}'** não foi encontrado nos documentos recentes.")

# --- RODAPÉ ---
st.markdown(f"""
<div class="footer">
    <div class="footer-credits">
        © {datetime.now().year} BT System • Desenvolvido por <strong>João Marcos</strong>
    </div>
    <div class="footer-disclaimer">
        ⚠️ <strong>Aviso Legal:</strong> Esta aplicação é independente e <u>não possui vínculo oficial</u> com o Governo de Rondônia.<br>
        A pesquisa utiliza apenas dados públicos disponíveis no portal <em>diof.ro.gov.br</em>.
    </div>
</div>
""", unsafe_allow_html=True)