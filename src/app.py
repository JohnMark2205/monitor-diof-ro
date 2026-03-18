import streamlit as st
import json
import os
import base64
from datetime import datetime
import requests
import time
import re  # Novo import para extrair datas via Regex

# --- CONFIGURAÇÃO DA PÁGINA (LAYOUT WIDE) ---
st.set_page_config(
    page_title="Monitor DIOF-RO", 
    page_icon="⚖️", 
    layout="wide",
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

# --- CSS VISUAL (V31) ---
st.markdown("""
    <style>
    /* 1. LAYOUT GERAL */
    .block-container { 
        padding-top: 3rem !important; 
        padding-bottom: 6rem; 
        max-width: 1400px !important;
    }
    
    /* 2. LOGO */
    .logo-box { text-align: center; width: 100%; margin-bottom: 20px; }
    .logo-box img { max-width: 250px; width: 70%; height: auto; }

    /* 3. TÍTULOS E STATUS */
    .main-title {
        text-align: center; font-weight: 800; font-size: 2rem; margin-bottom: 0; color: #f8fafc;
    }
    .sub-title {
        text-align: center; font-size: 0.9rem; opacity: 0.7; margin-bottom: 5px;
    }
    .status-text {
        text-align: center; font-size: 0.8rem; font-family: monospace; color: #9ca3af; margin-bottom: 20px;
    }

    /* 4. MENSAGEM DE ESCOPO */
    .scope-container {
        display: flex;
        justify-content: center; 
        width: 100%;
        margin-bottom: 30px;
    }
    .custom-info-box {
        background-color: rgba(37, 99, 235, 0.15); 
        border: 1px solid rgba(37, 99, 235, 0.3);
        color: #bfdbfe; 
        padding: 8px 20px;
        border-radius: 8px; 
        font-size: 0.9rem;
        width: fit-content; 
        text-align: center;
    }
    .custom-warning-box {
        background-color: rgba(234, 179, 8, 0.15); 
        border: 1px solid rgba(234, 179, 8, 0.3);
        color: #fef08a;
        padding: 8px 20px;
        border-radius: 8px;
        font-size: 0.9rem;
        width: fit-content;
        text-align: center;
    }

    /* 5. INPUTS */
    div[data-baseweb="input"] { border-radius: 8px !important; }
    div[data-baseweb="input"]:focus-within {
        border: 2px solid #2563eb !important;
        box-shadow: none !important;
    }
    .stTextInput input { caret-color: #2563eb !important; }
    
    /* 6. BOTÃO DE PESQUISA */
    .stButton button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        height: 48px;
        font-weight: 600 !important;
        border: none !important;
        width: 100%;
        white-space: nowrap !important; 
        overflow: hidden;
        transition: background 0.3s;
    }
    .stButton button:hover { background-color: #1d4ed8 !important; }

    /* 7. ESTILO DO CARD (INTERNO) */
    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #2563eb;
        margin-bottom: 2px;
        line-height: 1.2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .card-date {
        font-size: 0.7rem;
        color: #94a3b8; 
        margin-bottom: 12px;
        display: block;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 8px;
    }
    
    /* 8. TEXTO DE CONTEXTO */
    .found-text {
        font-size: 0.85rem;
        color: #e2e8f0; 
        margin-bottom: 8px;
        display: block;
    }
    .found-highlight {
        color: #34d399; 
        font-weight: 700;
    }
    
    /* 9. BOTÃO PDF */
    .pdf-button {
        display: block; width: 100%; 
        background-color: #2563eb; 
        color: white !important;
        text-decoration: none !important; 
        padding: 10px 0; 
        border-radius: 6px;
        font-size: 0.95rem;
        font-weight: 600; 
        text-align: center; 
        transition: all 0.2s ease-in-out;
        margin-bottom: 10px;
    }
    .pdf-button:hover {
        background-color: #1d4ed8; 
        transform: translateY(-1px);
    }
    
    /* 10. LEITURA RÁPIDA */
    .mobile-read-box {
        background-color: #0f172a; 
        color: #f1f5f9;            
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #334155;
        font-family: ui-sans-serif, system-ui, sans-serif;
        font-size: 0.85rem;
        line-height: 1.6; 
        max-height: 300px; 
        overflow-y: auto;
        white-space: pre-wrap;
        scrollbar-width: thin;
        scrollbar-color: #2563eb #0f172a;
    }
    .mobile-read-box::-webkit-scrollbar { width: 8px; }
    .mobile-read-box::-webkit-scrollbar-track { background: #0f172a; }
    .mobile-read-box::-webkit-scrollbar-thumb { background-color: #2563eb; border-radius: 4px; }

    /* 11. SELETOR DE PÁGINAS */
    div[role="radiogroup"] {
        margin-bottom: 15px;
    }
    div[role="radiogroup"] label {
        padding: 4px 12px; 
        font-size: 0.85rem;
        border-radius: 12px !important;
    }
    
    .status-highlight { color: #34d399; font-weight: 600; }
    
    .footer {
        text-align: center; margin-top: 50px; 
        font-size: 0.8rem; color: #64748b;
        padding: 20px; border-top: 1px solid rgba(255,255,255,0.1);
    }

    @media (prefers-color-scheme: light) {
        .main-title { color: #1e293b; }
        .card-date { color: #64748b; border-bottom: 1px solid #e2e8f0; }
        .footer { border-top: 1px solid #e2e8f0; }
        .status-highlight { color: #059669; }
        .found-text { color: #334155; }
        .found-highlight { color: #059669; }
        
        .custom-info-box {
            background-color: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1e40af;
        }
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
            all_data = json.loads(content) if content else []
            # TRAVA DE 30 EDIÇÕES: 
            # Pega apenas os 30 primeiros itens (mais recentes) da base de dados.
            return all_data[:30] 
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
        matches_map = {} 
        found_any = False
        
        try:
            pages = doc.get('pages_content', [])
            for page in pages:
                if term_lower in page['text'].lower():
                    page_num = str(page['number']).strip()
                    matches_map[page_num] = page['text']
                    found_any = True

            if not found_any and 'content' in doc:
                 if term_lower in doc['content'].lower():
                    matches_map["9999"] = doc['content']
                    found_any = True
        except: continue
            
        if found_any:
            sorted_pages = sorted(matches_map.keys(), key=lambda x: int(x) if x.isdigit() else 9999)
            results.append({
                "title": doc['title'],
                "url": doc['url'],
                "matches": matches_map,
                "pages": sorted_pages
            })
    return results

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Painel de Controle")
    st.info("O sistema verifica novas edições automaticamente a cada 30 minutos.")
    st.divider()
    st.write("**Precisa de ajuda?**")
    st.write("Achou algum erro?")
    st.link_button("📧 Entrar em Contato", url=CONTACT_FORM_URL, use_container_width=True)

# --- HEADER (Centralizado) ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    img_b64 = get_base64_image(LOGO_PATH)
    if img_b64:
        st.markdown(f"""<div class="logo-box"><img src="data:image/png;base64,{img_b64}"></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style='text-align: center; margin-bottom: 20px;'><h1 style='color:#0068c9;'>BT</h1></div>""", unsafe_allow_html=True)

    data = load_data()
    status = load_status()
    global_last_run = status['last_run'] if (status and 'last_run' in status) else "Data desconhecida"

    st.markdown(f"""
        <h1 class="main-title">Buscador de Termos</h1>
        <p class="sub-title">Monitoramento Automatizado</p>
        <p class="status-text">✅ Última verificação: <span class="status-highlight">{global_last_run}</span></p>
    """, unsafe_allow_html=True)

    # --- MENSAGEM DE ESCOPO CENTRALIZADA COM DATA DINÂMICA ---
    if data:
        num_edicoes = len(data)
        edicao_mais_antiga = data[-1] # A última da lista truncada em 30
        
        # 1. Tenta extrair a data dos campos nativos
        data_inicio = edicao_mais_antiga.get('date') or edicao_mais_antiga.get('scraped_at')
        if data_inicio:
            data_inicio = data_inicio.split(" ")[0] # Se tiver hora, remove
        else:
            # 2. Se falhar, procura por um padrão de data (DD/MM/AAAA ou DD-MM-AAAA) no título
            titulo = edicao_mais_antiga.get('title', '')
            match = re.search(r'\d{2}[-/]\d{2}[-/]\d{4}', titulo)
            if match:
                data_inicio = match.group(0).replace('-', '/')
            else:
                data_inicio = "Data desconhecida"

        # Mensagem HTML atualizada com a data
        st.markdown(f"""
            <div class="scope-container">
                <div class="custom-info-box">
                    📂 <strong>Escopo:</strong> Monitorando as <strong>{num_edicoes} últimas edições</strong> (desde <em>{data_inicio}</em>).
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="scope-container">
                <div class="custom-warning-box">
                    ⚠️ Base de dados vazia.
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- FORM DE BUSCA ---
c_left, c_center, c_right = st.columns([1, 3, 1])

with c_center:
    st.write("O que você procura?")
    with st.form(key='search_form'):
        col_in, col_btn = st.columns([4, 1], gap="small", vertical_alignment="bottom")
        with col_in:
            query = st.text_input(label="Busca", placeholder="Digite Nome, CPF, Matrícula...", label_visibility="collapsed")
        with col_btn:
            submit_button = st.form_submit_button(label="🔍 Pesquisar")

# --- RESULTADOS (V31) ---
if submit_button or query:
    st.divider()
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
            
            num_cols = 3
            cols = st.columns(num_cols)
            
            for i, res in enumerate(results):
                with cols[i % num_cols]:
                    with st.container(border=True):
                        base_url = res['url'].strip().split("?")[0]
                        
                        # 1. TÍTULO E DATA
                        st.markdown(f"""
                            <div class="card-title" title="{res['title']}">📄 {res['title']}</div>
                            <span class="card-date">Atualizado em: {global_last_run}</span>
                        """, unsafe_allow_html=True)
                        
                        # 2. CONTEXTO E SELETOR DE PÁGINAS
                        available_pages = res['pages']
                        selected_page_num = available_pages[0]

                        if len(available_pages) > 1:
                            st.markdown(f"""<span class="found-text">Encontrado em <span class="found-highlight">{len(available_pages)}</span> páginas:</span>""", unsafe_allow_html=True)
                            selected_page_num = st.radio(
                                "Seletor de páginas", 
                                options=available_pages,
                                horizontal=True,
                                label_visibility="collapsed",
                                key=f"sel_{i}_{base_url}"
                            )
                        else:
                             st.markdown(f"""<span class="found-text">Encontrado na página <span class="found-highlight">{selected_page_num}</span></span>""", unsafe_allow_html=True)
                        
                        # 3. BOTÃO DE AÇÃO
                        if selected_page_num != "9999" and selected_page_num.isdigit():
                            link = f"{base_url}#page={selected_page_num}"
                            btn_txt = f"Abrir Pág. {selected_page_num}"
                        else:
                            link = base_url
                            btn_txt = "Abrir Original"
                        
                        st.markdown(f"""<a href="{link}" target="_blank" class="pdf-button">{btn_txt}</a>""", unsafe_allow_html=True)

                        # 4. EXPANDER
                        full_text = res['matches'].get(selected_page_num, "...")
                        with st.expander("📱 Ler Texto"):
                            st.markdown(f"""<div class="mobile-read-box">{full_text}</div>""", unsafe_allow_html=True)

        else:
            st.warning(f"O termo **'{query}'** não foi encontrado.")

# --- RODAPÉ ---
st.markdown(f"""
<div class="footer">
    © {datetime.now().year} BT System • Desenvolvido por <strong>João Marcos</strong><br>
    <span style="opacity:0.7; font-size:0.7rem;">Dados públicos do portal diof.ro.gov.br</span>
</div>
""", unsafe_allow_html=True)