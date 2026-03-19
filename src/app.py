import streamlit as st
import json
import os
import base64
from datetime import datetime
import requests
import time
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Monitor DIOF-RO", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- INICIALIZAÇÃO DO CONTROLE DE SESSÃO (Para o Pop-up) ---
if 'pesquisa_realizada' not in st.session_state:
    st.session_state.pesquisa_realizada = 0
if 'modal_exibido' not in st.session_state:
    st.session_state.modal_exibido = False

# --- CONFIGURAÇÃO DE CAMINHOS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
DB_FILE = os.path.join(root_dir, 'data', 'dados.json')
STATUS_FILE = os.path.join(root_dir, 'data', 'status.json')
LOGO_PATH = os.path.join(root_dir, 'assets', 'logo_diof.png')

# --- LINKS EXTERNOS ---
CONTACT_FORM_URL = "https://forms.gle/ZyjbbLg47n6uVNAz9"

# ✅ SEU LINK OFICIAL INSERIDO AQUI
ALERT_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdeDFLj0NoYpT5HhwFisnSNeCxjE2d-9AueiRAH99Rt5PFuCQ/viewform?usp=header" 

# --- CSS VISUAL (V36 - BOTÃO FLUTUANTE) ---
st.markdown("""
    <style>
    .block-container { padding-top: 3rem !important; padding-bottom: 6rem; max-width: 1400px !important;}
    .logo-box { text-align: center; width: 100%; margin-bottom: 20px; }
    .logo-box img { max-width: 250px; width: 70%; height: auto; }
    .main-title { text-align: center; font-weight: 800; font-size: 2rem; margin-bottom: 0; color: #f8fafc; }
    .status-text { text-align: center; font-size: 0.8rem; font-family: monospace; color: #9ca3af; margin-bottom: 30px; }
    
    /* === BOTÃO FLUTUANTE (FIXO NO CANTO INFERIOR DIREITO) === */
    .floating-btn {
        position: fixed;
        bottom: 30px;
        right: 30px;
        background-color: #10b981;
        color: white !important;
        border-radius: 50px;
        padding: 15px 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
        z-index: 9999;
        text-decoration: none !important;
        font-weight: 800;
        font-size: 1rem;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .floating-btn:hover {
        background-color: #059669;
        transform: scale(1.05) translateY(-5px);
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.5);
    }

    div[data-baseweb="input"] { border-radius: 8px !important; }
    div[data-baseweb="input"]:focus-within { border: 2px solid #2563eb !important; box-shadow: none !important; }
    .stTextInput input { caret-color: #2563eb !important; }
    .stButton button { background-color: #2563eb !important; color: white !important; border-radius: 8px !important; height: 48px; font-weight: 600 !important; border: none !important; width: 100%; transition: background 0.3s; }
    .stButton button:hover { background-color: #1d4ed8 !important; }
    
    .card-title { font-size: 1.05rem; font-weight: 700; color: #60a5fa; margin-bottom: 2px; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .card-date { font-size: 0.7rem; color: #94a3b8; margin-bottom: 12px; display: block; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px; }
    .found-text { font-size: 0.85rem; color: #e2e8f0; margin-bottom: 8px; display: block; }
    .found-highlight { color: #34d399; font-weight: 700; }
    .pdf-button { display: block; width: 100%; background-color: #2563eb; color: white !important; text-decoration: none !important; padding: 10px 0; border-radius: 6px; font-size: 0.95rem; font-weight: 600; text-align: center; transition: all 0.2s ease-in-out; margin-bottom: 10px; }
    .pdf-button:hover { background-color: #1d4ed8; transform: translateY(-1px); }
    .mobile-read-box { background-color: #0f172a; color: #f1f5f9; padding: 12px; border-radius: 6px; border: 1px solid #334155; font-size: 0.85rem; line-height: 1.6; max-height: 300px; overflow-y: auto; white-space: pre-wrap; scrollbar-width: thin; scrollbar-color: #2563eb #0f172a; }
    
    .status-highlight { color: #34d399; font-weight: 600; }
    .footer { text-align: center; margin-top: 50px; font-size: 0.8rem; color: #64748b; padding: 20px; border-top: 1px solid rgba(255,255,255,0.1); }
    
    @media (prefers-color-scheme: light) {
        .main-title { color: #1e293b; }
        .card-title { color: #2563eb; }
        .card-date { color: #64748b; border-bottom: 1px solid #e2e8f0; }
        .footer { border-top: 1px solid #e2e8f0; }
        .status-highlight { color: #059669; }
        .found-text { color: #334155; }
        .found-highlight { color: #059669; }
    }
    </style>
""", unsafe_allow_html=True)

# --- INJEÇÃO DO BOTÃO FLUTUANTE HTML ---
st.markdown(f"""
    <a href="{ALERT_FORM_URL}" target="_blank" class="floating-btn">
        🔔 Criar Alerta
    </a>
""", unsafe_allow_html=True)

# --- FUNÇÕES NUCLEARES E DE DATA ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file: return base64.b64encode(img_file.read()).decode()
    return None

def load_status():
    if not os.path.exists(STATUS_FILE): return None
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return None

def filter_last_month_data(all_data, status_data):
    ref_date = datetime.now()
    if status_data and 'last_run' in status_data:
        try: ref_date = datetime.strptime(status_data['last_run'], "%d/%m/%Y %H:%M:%S")
        except: pass
    month = ref_date.month - 1
    year = ref_date.year
    if month == 0:
        month = 12
        year -= 1
    day = ref_date.day
    while True:
        try:
            limit_date = ref_date.replace(year=year, month=month, day=day)
            break
        except ValueError: day -= 1
            
    limit_date_str = limit_date.strftime("%d/%m/%Y")
    filtered_data = []
    
    for doc in all_data:
        doc_date = None
        raw_date = doc.get('date') or doc.get('scraped_at')
        if raw_date and raw_date != 'Data desc.':
            date_part = raw_date.split(" ")[0]
            try:
                if "-" in date_part and len(date_part.split("-")[0]) == 4: doc_date = datetime.strptime(date_part, "%Y-%m-%d")
                elif "/" in date_part: doc_date = datetime.strptime(date_part, "%d/%m/%Y")
            except: pass
        if not doc_date:
            titulo = doc.get('title', '')
            match = re.search(r'(\d{2})[-/](\d{2})[-/](\d{4})', titulo)
            if match:
                dia, mes, ano = match.groups()
                try: doc_date = datetime(int(ano), int(mes), int(dia))
                except: pass
        if doc_date:
            if doc_date.date() >= limit_date.date(): filtered_data.append(doc)
        else: filtered_data.append(doc)
            
    return filtered_data, limit_date_str

def load_filtered_data():
    if not os.path.exists(DB_FILE): return [], "Data desconhecida"
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            all_data = json.loads(content) if content else []
            status_data = load_status()
            filtered, limit_date_str = filter_last_month_data(all_data, status_data)
            return filtered, limit_date_str
    except: return [], "Data desconhecida"

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
            results.append({"title": doc['title'], "url": doc['url'], "matches": matches_map, "pages": sorted_pages})
    return results

# --- FUNÇÃO DO POP-UP (MODAL) ---
@st.dialog("🤖 Automatize sua pesquisa!")
def mostrar_modal_alerta(termo_pesquisado, encontrou_resultados):
    if encontrou_resultados:
        st.write(f"Encontramos o termo **'{termo_pesquisado}'** nas edições recentes.")
    else:
        st.write(f"Não encontramos o termo **'{termo_pesquisado}'** hoje.")
        
    st.write("Que tal não precisar fazer essa busca todos os dias? Cadastre seu termo e receba um **alerta por e-mail** assim que ele sair no Diário Oficial.")
    
    st.markdown(f"""
        <a href="{ALERT_FORM_URL}" target="_blank" style="display: block; background-color: #10b981; color: white; text-align: center; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 10px; margin-bottom: 15px;">
            ✅ Criar Alerta Gratuito Agora
        </a>
    """, unsafe_allow_html=True)
    
    if st.button("Agora não, obrigado"):
        st.rerun() # Atualiza a tela e fecha o modal

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ BT System")
    st.info("O sistema verifica novas edições no portal diof.ro.gov.br a cada 30 minutos.")
    st.divider()
    st.write("**Dúvidas ou Suporte?**")
    st.link_button("📧 Entrar em Contato", url=CONTACT_FORM_URL, use_container_width=True)

# --- HEADER (Centralizado) ---
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    img_b64 = get_base64_image(LOGO_PATH)
    if img_b64: st.markdown(f"""<div class="logo-box"><img src="data:image/png;base64,{img_b64}"></div>""", unsafe_allow_html=True)
    else: st.markdown("""<div style='text-align: center; margin-bottom: 20px;'><h1 style='color:#0068c9;'>BT</h1></div>""", unsafe_allow_html=True)

    status = load_status()
    global_last_run = status['last_run'] if (status and 'last_run' in status) else "Data desconhecida"

    st.markdown(f"""
        <h1 class="main-title">Monitor DIOF-RO</h1>
        <p class="status-text">✅ Escopo: Último mês (Atualizado em: <span class="status-highlight">{global_last_run}</span>)</p>
    """, unsafe_allow_html=True)

data, date_limit_str = load_filtered_data()

# --- PESQUISA ---
c_search_l, c_search_c, c_search_r = st.columns([1, 3, 1])
with c_search_c:
    st.write("Digite um nome, OAB ou CPF para buscar no acervo recente:")
    with st.form(key='search_form'):
        col_in, col_btn = st.columns([4, 1], gap="small", vertical_alignment="bottom")
        with col_in: query = st.text_input(label="Busca", placeholder="O que você procura?", label_visibility="collapsed")
        with col_btn: submit_button = st.form_submit_button(label="🔍 Buscar")

# --- LÓGICA DE RESULTADOS E POP-UP ---
if submit_button or query:
    if not query: 
        st.warning("⚠️ Digite algo para pesquisar.")
    elif not data: 
        st.error("Sem dados no período para pesquisar.")
    else:
        # Aumenta o contador de pesquisas
        if submit_button:
            st.session_state.pesquisa_realizada += 1

        start_time = datetime.now()
        results = search_local(query, data)
        duration = (datetime.now() - start_time).total_seconds()
        
        # --- GATILHO DO POP-UP (Aparece só na 1ª vez) ---
        if st.session_state.pesquisa_realizada == 1 and not st.session_state.modal_exibido:
            st.session_state.modal_exibido = True
            mostrar_modal_alerta(query, len(results) > 0)
        
        if results:
            st.success(f"🔍 Encontrado em {len(results)} documentos ({duration:.3f}s)")
            num_cols = 3
            cols = st.columns(num_cols)
            
            for i, res in enumerate(results):
                with cols[i % num_cols]:
                    with st.container(border=True):
                        base_url = res['url'].strip().split("?")[0]
                        st.markdown(f"""<div class="card-title" title="{res['title']}">📄 {res['title']}</div><span class="card-date">Atualizado em: {global_last_run}</span>""", unsafe_allow_html=True)
                        
                        available_pages = res['pages']
                        selected_page_num = available_pages[0]

                        if len(available_pages) > 1:
                            st.markdown(f"""<span class="found-text">Encontrado em <span class="found-highlight">{len(available_pages)}</span> páginas:</span>""", unsafe_allow_html=True)
                            selected_page_num = st.radio("Seletor de páginas", options=available_pages, horizontal=True, label_visibility="collapsed", key=f"sel_{i}_{base_url}")
                        else:
                             st.markdown(f"""<span class="found-text">Encontrado na página <span class="found-highlight">{selected_page_num}</span></span>""", unsafe_allow_html=True)
                        
                        if selected_page_num != "9999" and selected_page_num.isdigit():
                            link = f"{base_url}#page={selected_page_num}"
                            btn_txt = f"Abrir Pág. {selected_page_num}"
                        else:
                            link = base_url
                            btn_txt = "Abrir Original"
                        
                        st.markdown(f"""<a href="{link}" target="_blank" class="pdf-button">{btn_txt}</a>""", unsafe_allow_html=True)

                        full_text = res['matches'].get(selected_page_num, "...")
                        with st.expander("📱 Ler Trecho"):
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