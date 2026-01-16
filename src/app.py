import streamlit as st
import json
import os
import base64
from datetime import datetime
import requests
import time

# --- CONFIGURAÇÃO DA PÁGINA (LAYOUT WIDE PARA CABER 3 COLUNAS) ---
st.set_page_config(
    page_title="Monitor DIOF-RO", 
    page_icon="⚖️", 
    layout="wide", # MUDANÇA IMPORTANTE: Layout Wide para caber o grid
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

# --- CSS VISUAL (V25 - GRID & CARD SYSTEM) ---
st.markdown("""
    <style>
    /* 1. LAYOUT GERAL */
    .block-container { 
        padding-top: 3rem !important; 
        padding-bottom: 6rem; 
        max-width: 1200px !important; /* Limita a largura para não esticar demais em monitores gigantes */
    }
    
    /* 2. LOGO */
    .logo-box { text-align: center; width: 100%; margin-bottom: 20px; }
    .logo-box img { max-width: 250px; width: 70%; height: auto; }

    /* 3. TÍTULOS E STATUS */
    .main-title {
        text-align: center;
        font-weight: 800;
        font-size: 2rem;
        margin-bottom: 0;
        color: #f8fafc; /* Cor clara padrão */
    }
    .sub-title {
        text-align: center;
        font-size: 0.9rem;
        opacity: 0.7;
        margin-bottom: 5px;
    }
    .status-text {
        text-align: center;
        font-size: 0.8rem;
        font-family: monospace;
        color: #9ca3af;
        margin-bottom: 30px;
    }

    /* 4. INPUTS */
    div[data-baseweb="input"] { border-radius: 8px !important; }
    div[data-baseweb="input"]:focus-within {
        border: 2px solid #2563eb !important;
        box-shadow: none !important;
    }
    .stTextInput input { caret-color: #2563eb !important; }
    
    /* 5. BOTÃO DE PESQUISA */
    .stButton button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 8px !important;
        height: 48px;
        font-weight: 600 !important;
        border: none !important;
        width: 100%;
        transition: background 0.3s;
    }
    .stButton button:hover { background-color: #1d4ed8 !important; }

    /* 6. ESTILO DO CARD (INTERNO) */
    .card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #2563eb;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .card-date {
        font-size: 0.75rem;
        color: #64748b;
        margin-bottom: 12px;
        display: block;
    }
    
    /* 7. SNIPPET DE TEXTO (Dentro do Card) */
    .snippet-box {
        background: #1e293b; 
        color: #e2e8f0;      
        padding: 10px; 
        border-radius: 6px; 
        font-family: monospace; 
        font-size: 0.8rem; 
        margin-bottom: 10px;
        border: 1px solid #334155; 
        line-height: 1.4;
        min-height: 80px; /* Altura mínima para alinhar os cards */
    }
    
    /* 8. BOTÃO PDF (Dentro do Card) */
    .pdf-button {
        display: block; width: 100%; 
        background-color: #2563eb; 
        color: white !important;
        text-decoration: none !important; 
        padding: 8px 0; 
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 600; 
        text-align: center; 
        margin-top: 10px; 
        margin-bottom: 10px;
        transition: all 0.2s ease-in-out;
    }
    .pdf-button:hover {
        background-color: #1d4ed8; 
        transform: translateY(-1px);
    }
    
    /* 9. LEITURA RÁPIDA (Dentro do Card) */
    .mobile-read-box {
        background-color: #0f172a; 
        color: #f1f5f9;            
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #334155;
        font-family: ui-sans-serif, system-ui, sans-serif;
        font-size: 0.85rem;
        line-height: 1.6; 
        max-height: 300px; /* Menor altura para caber no grid */
        overflow-y: auto;
        white-space: pre-wrap;
        scrollbar-width: thin;
        scrollbar-color: #2563eb #0f172a;
    }
    .mobile-read-box::-webkit-scrollbar { width: 8px; }
    .mobile-read-box::-webkit-scrollbar-track { background: #0f172a; }
    .mobile-read-box::-webkit-scrollbar-thumb { background-color: #2563eb; border-radius: 4px; }

    /* 10. SELETOR DE PÁGINAS (Compacto) */
    div[role="radiogroup"] label {
        padding: 2px 8px;
        font-size: 0.8rem;
    }
    
    .status-highlight { color: #34d399; font-weight: 600; }
    
    .footer {
        text-align: center; margin-top: 50px; 
        font-size: 0.8rem; color: #64748b;
        padding: 20px; border-top: 1px solid rgba(255,255,255,0.1);
    }

    /* MEDIA QUERY LIGHT MODE */
    @media (prefers-color-scheme: light) {
        .main-title { color: #1e293b; }
        .card-date { color: #64748b; }
        .footer { border-top: 1px solid #e2e8f0; }
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
        matches_map = {} 
        snippet = ""
        found_any = False
        
        try:
            pages = doc.get('pages_content', [])
            for page in pages:
                if term_lower in page['text'].lower():
                    page_num = str(page['number']).strip()
                    matches_map[page_num] = page['text']
                    found_any = True
                    if not snippet:
                        idx = page['text'].lower().find(term_lower)
                        start = max(0, idx - 40)
                        end = min(len(page['text']), idx + 100)
                        snippet = page['text'][start:end].replace("\n", " ")

            if not found_any and 'content' in doc:
                 if term_lower in doc['content'].lower():
                    matches_map["9999"] = doc['content']
                    idx = doc['content'].lower().find(term_lower)
                    snippet = doc['content'][idx:idx+100]
                    found_any = True
        except: continue
            
        if found_any:
            sorted_pages = sorted(matches_map.keys(), key=lambda x: int(x) if x.isdigit() else 9999)
            results.append({
                "title": doc['title'],
                "url": doc['url'],
                "date": doc.get('scraped_at', 'Data desc.'),
                "matches": matches_map,
                "pages": sorted_pages,
                "snippet": snippet
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
# Usamos colunas para centralizar a imagem no layout Wide
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    img_b64 = get_base64_image(LOGO_PATH)
    if img_b64:
        st.markdown(f"""<div class="logo-box"><img src="data:image/png;base64,{img_b64}"></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style='text-align: center; margin-bottom: 20px;'><h1 style='color:#0068c9;'>BT</h1></div>""", unsafe_allow_html=True)

    # Status e Título
    data = load_data()
    status = load_status()
    display_date = status['last_run'] if (status and 'last_run' in status) else "Desconhecido"

    st.markdown(f"""
        <h1 class="main-title">Buscador de Termos</h1>
        <p class="sub-title">Monitoramento Automatizado</p>
        <p class="status-text">✅ Última verificação: <span class="status-highlight">{display_date}</span></p>
    """, unsafe_allow_html=True)

    # Info de Escopo
    if data:
        st.info(f"📂 **Escopo:** Monitorando as **{len(data)} últimas edições** (apenas capa do portal).")
    else:
        st.warning("⚠️ Base de dados vazia.")

    # Form de Busca
    st.write("O que você procura?")
    with st.form(key='search_form'):
        col_in, col_btn = st.columns([4, 1], gap="small")
        with col_in:
            query = st.text_input(label="Busca", placeholder="Digite Nome, CPF, Matrícula...", label_visibility="collapsed")
        with col_btn:
            submit_button = st.form_submit_button(label="🔍 Pesquisar")

# --- RESULTADOS (GRID LAYOUT) ---
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
            
            # --- CONFIGURAÇÃO DO GRID (3 COLUNAS) ---
            num_cols = 3
            cols = st.columns(num_cols)
            
            for i, res in enumerate(results):
                # Escolhe a coluna certa (0, 1 ou 2) baseado no índice
                with cols[i % num_cols]:
                    
                    # CADA RESULTADO É UM CONTAINER "CARTÃO"
                    with st.container(border=True):
                        
                        # 1. Cabeçalho do Card
                        base_url = res['url'].strip().split("?")[0]
                        st.markdown(f"""
                            <div class="card-title">📄 {res['title']}</div>
                            <span class="card-date">{res['date']}</span>
                        """, unsafe_allow_html=True)
                        
                        # 2. Snippet (Texto fixo de prévia)
                        st.markdown(f"""<div class="snippet-box">...{res['snippet']}...</div>""", unsafe_allow_html=True)

                        # 3. Lógica de Páginas (Interativa)
                        available_pages = res['pages']
                        selected_page_num = available_pages[0]

                        if len(available_pages) > 1:
                            st.caption(f"Encontrado em {len(available_pages)} pgs:")
                            selected_page_num = st.radio(
                                "Páginas:",
                                options=available_pages,
                                horizontal=True,
                                label_visibility="collapsed",
                                key=f"sel_{i}_{base_url}" # Key única para o grid
                            )
                        else:
                            st.caption(f"Página única: {selected_page_num}")

                        # 4. Link Dinâmico
                        if selected_page_num != "9999" and selected_page_num.isdigit():
                            link = f"{base_url}#page={selected_page_num}"
                            btn_txt = f"Abrir Pág. {selected_page_num}"
                        else:
                            link = base_url
                            btn_txt = "Abrir Original"
                        
                        st.markdown(f"""<a href="{link}" target="_blank" class="pdf-button">{btn_txt}</a>""", unsafe_allow_html=True)

                        # 5. Expander (Fica dentro do cartão)
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