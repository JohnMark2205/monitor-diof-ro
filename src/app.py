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
CONTACT_FORM_URL = "https://forms.gle/ZyjbbLg47n6uVNAz9"

# --- CSS VISUAL (V24 - PAGINAÇÃO DINÂMICA) ---
st.markdown("""
    <style>
    /* 1. LAYOUT GERAL */
    .block-container { 
        padding-top: 4.5rem !important; 
        padding-bottom: 6rem; 
    }
    
    /* 2. LOGO */
    .logo-box { text-align: center; width: 100%; margin-bottom: 15px; }
    .logo-box img { max-width: 300px; width: 80%; height: auto; }

    /* 3. INPUTS */
    div[data-baseweb="input"] { border-radius: 8px !important; }
    div[data-baseweb="input"]:focus-within {
        border: 2px solid #2563eb !important;
        box-shadow: none !important;
    }
    .stTextInput input { caret-color: #2563eb !important; }
    
    /* 4. BOTÕES GERAIS */
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

    /* 5. CARDS DE RESULTADO */
    .result-card {
        background-color: rgba(37, 99, 235, 0.05); 
        border: 1px solid rgba(37, 99, 235, 0.2);
        padding: 16px; 
        border-radius: 12px; 
        margin-bottom: 10px; /* Reduzi margem pois agora tem controles dentro */
        border-left: 5px solid #2563eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* 6. SNIPPET DE TEXTO */
    .snippet-box {
        background: #1e293b; 
        color: #e2e8f0;      
        padding: 12px; 
        border-radius: 8px; 
        font-family: monospace; 
        font-size: 0.85rem; 
        margin: 12px 0;
        border: 1px solid #334155; 
        line-height: 1.4;
    }
    
    /* 7. BOTÃO PDF (Dentro do HTML) */
    .pdf-button {
        display: block; width: 100%; background-color: #2563eb; color: white !important;
        text-decoration: none !important; padding: 12px 0; border-radius: 8px;
        font-weight: 600; text-align: center; margin-top: 15px; border: none;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); transition: all 0.2s ease-in-out;
    }
    .pdf-button:hover {
        background-color: #1d4ed8; transform: translateY(-2px);
    }
    
    /* 8. LEITURA RÁPIDA (SCROLLBAR AZUL) */
    .mobile-read-box {
        background-color: #0f172a; 
        color: #f1f5f9;            
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #334155;
        font-family: ui-sans-serif, system-ui, -apple-system, sans-serif;
        font-size: 0.95rem;
        line-height: 1.7; 
        max-height: 400px;
        overflow-y: auto;
        -webkit-overflow-scrolling: touch; 
        white-space: pre-wrap;
        margin-top: 10px;
        scrollbar-width: thin;
        scrollbar-color: #2563eb #0f172a;
    }
    .mobile-read-box::-webkit-scrollbar { width: 10px; }
    .mobile-read-box::-webkit-scrollbar-track { background: #0f172a; border-radius: 4px; }
    .mobile-read-box::-webkit-scrollbar-thumb { 
        background-color: #2563eb !important; 
        border-radius: 6px; 
        border: 2px solid #0f172a; 
    }

    .streamlit-expanderHeader {
        font-size: 0.9rem; font-weight: 600; color: #2563eb;
        background-color: rgba(37, 99, 235, 0.05); border-radius: 8px;
    }

    /* 9. ESTILO DO SELETOR DE PÁGINAS (ST.RADIO) */
    /* Deixa o radio button com cara de botões de navegação */
    div[role="radiogroup"] {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 10px;
    }
    div[role="radiogroup"] label {
        background-color: rgba(37, 99, 235, 0.1);
        border: 1px solid rgba(37, 99, 235, 0.3);
        padding: 4px 12px;
        border-radius: 20px;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.85rem;
    }
    div[role="radiogroup"] label:hover {
        background-color: rgba(37, 99, 235, 0.2);
    }
    /* Item Selecionado */
    div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
        background-color: #2563eb;
    }

    .status-highlight { color: #34d399; font-weight: 600; }
    
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: rgba(14, 17, 23, 0.98); color: #9ca3af; text-align: center;
        padding: 15px 20px; z-index: 99999; border-top: 1px solid rgba(255,255,255,0.1);
        display: flex; flex-direction: column; gap: 5px; backdrop-filter: blur(5px);
    }
    .footer-credits { font-size: 0.85rem; font-weight: 600; color: #d1d5db; }
    .footer-disclaimer { font-size: 0.7rem; opacity: 0.8; line-height: 1.3; }
    
    @media (prefers-color-scheme: light) {
        .result-card { background-color: #f8fafc; border: 1px solid #e2e8f0; }
        .footer { background-color: rgba(255, 255, 255, 0.98); color: #4b5563; border-top: 1px solid #e5e7eb; }
        .footer-credits { color: #1f2937; }
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

# --- NOVA LÓGICA DE BUSCA: CAPTURA MÚLTIPLAS PÁGINAS ---
def search_local(term, data):
    results = []
    term_lower = term.lower()
    
    for doc in data:
        matches_map = {} # Dicionário: {'15': 'Texto completo da pág 15', '20': 'Texto da 20'}
        snippet = ""
        found_any = False
        
        try:
            pages = doc.get('pages_content', [])
            for page in pages:
                if term_lower in page['text'].lower():
                    page_num = str(page['number']).strip()
                    # Salva o texto desta página específica
                    matches_map[page_num] = page['text']
                    found_any = True
                    
                    # Gera um snippet só da primeira ocorrência para mostrar no card principal
                    if not snippet:
                        idx = page['text'].lower().find(term_lower)
                        start = max(0, idx - 40)
                        end = min(len(page['text']), idx + 100)
                        snippet = page['text'][start:end].replace("\n", " ")

            # Fallback para dados antigos (sem pages_content separado)
            if not found_any and 'content' in doc:
                 if term_lower in doc['content'].lower():
                    matches_map["9999"] = doc['content'] # 9999 indica "texto corrido"
                    idx = doc['content'].lower().find(term_lower)
                    snippet = doc['content'][idx:idx+100]
                    found_any = True
        except: continue
            
        if found_any:
            # Ordena as páginas encontradas (numérico)
            sorted_pages = sorted(matches_map.keys(), key=lambda x: int(x) if x.isdigit() else 9999)
            
            results.append({
                "title": doc['title'],
                "url": doc['url'],
                "date": doc.get('scraped_at', 'Data desc.'),
                "matches": matches_map,      # Mapeamento completo
                "pages": sorted_pages,       # Lista ordenada de páginas
                "snippet": snippet           # Trecho para o card
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

# --- HEADER ---
img_b64 = get_base64_image(LOGO_PATH)
if img_b64:
    st.markdown(f"""
        <div class="logo-box">
            <img src="data:image/png;base64,{img_b64}">
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
            
            # --- LOOP DE RESULTADOS ---
            for i, res in enumerate(results):
                base_url = res['url'].strip()
                if "?" in base_url: base_url = base_url.split("?")[0]
                
                # --- INTERATIVIDADE: SELETOR DE PÁGINAS ---
                # Se tiver mais de uma página, mostra o seletor. Se só tem uma, seleciona ela direto.
                available_pages = res['pages']
                selected_page_num = available_pages[0] # Padrão: primeira encontrada
                
                # HTML do Card (Topo)
                card_header = f"""
                <div class="result-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                        <h3 style="margin:0; font-size:1.1rem; color:#2563eb; line-height:1.2;">📄 {res['title']}</h3>
                        <span style="font-size:0.75rem; color:#6b7280; white-space:nowrap; margin-left:10px;">{res['date']}</span>
                    </div>
                """
                st.markdown(card_header, unsafe_allow_html=True)
                
                # WIDGET DE SELEÇÃO (INTERATIVO)
                # Usamos st.radio horizontal para parecer "tabs" ou botões
                if len(available_pages) > 1:
                    st.write(f"**Encontrado em {len(available_pages)} páginas.** Selecione para visualizar:")
                    # Unique key é crucial aqui! Usamos URL + Index do loop
                    selected_page_num = st.radio(
                        "Selecione a página:",
                        options=available_pages,
                        horizontal=True,
                        label_visibility="collapsed",
                        key=f"page_sel_{i}_{base_url}"
                    )
                else:
                    st.caption(f"Encontrado na Página: **{selected_page_num}**")

                # --- LÓGICA DINÂMICA (BASEADA NA SELEÇÃO) ---
                # 1. Determina o Link
                if selected_page_num != "9999" and selected_page_num.isdigit():
                    dynamic_link = f"{base_url}#page={selected_page_num}"
                    btn_text = f"Abrir PDF na Pág. {selected_page_num}"
                else:
                    dynamic_link = base_url
                    btn_text = "Abrir PDF Original"
                
                # 2. Determina o Texto Completo
                full_text_display = res['matches'].get(selected_page_num, "Texto não disponível.")

                # HTML do Card (Parte de baixo com botão dinâmico)
                card_footer = f"""
                    <div class="snippet-box">
                        ...{res['snippet']}...
                    </div>
                    <a href="{dynamic_link}" target="_blank" class="pdf-button">
                        {btn_text}
                    </a>
                </div>
                """
                st.markdown(card_footer, unsafe_allow_html=True)
                
                # EXPANDER DE LEITURA (DINÂMICO)
                with st.expander(f"📱 Leitura Rápida (Pág. {selected_page_num})"):
                    st.markdown(f"""
                    <div class="mobile-read-box">
                        {full_text_display}
                    </div>
                    <p style="font-size:0.7rem; color:#9ca3af; margin-top:5px; text-align:center;">
                        Texto extraído da página {selected_page_num}. Role para ler.
                    </p>
                    """, unsafe_allow_html=True)
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