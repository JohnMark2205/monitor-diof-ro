import streamlit as st
import json
import os
import base64
from datetime import datetime

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
LOGO_PATH = os.path.join(root_dir, 'assets', 'logo_diof.png')

# --- CSS VISUAL ---
st.markdown("""
    <style>
    .block-container { padding-top: 2rem; padding-bottom: 8rem; }
    .logo-container { display: flex; justify-content: center; align-items: center; width: 100%; margin-bottom: 20px; }
    
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
        background: rgba(0,0,0,0.2); 
        padding: 12px; 
        border-radius: 8px; 
        font-family: monospace; 
        font-size: 0.85rem; 
        margin: 12px 0;
        color: #e5e7eb;
        border: 1px solid rgba(255,255,255,0.05);
        line-height: 1.4;
    }
    
    .pdf-button {
        display: block;
        width: 100%;
        background-color: #2563eb;
        color: white !important;
        text-decoration: none !important;
        padding: 12px 0;
        border-radius: 8px;
        font-weight: 600;
        text-align: center;
        margin-top: 15px;
        border: none;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
        transition: all 0.2s ease-in-out;
    }
    .pdf-button:hover {
        background-color: #1d4ed8;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(37, 99, 235, 0.3);
    }
    
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: rgba(14, 17, 23, 0.98);
        color: #9ca3af; text-align: center; padding: 15px 20px; 
        z-index: 99999; border-top: 1px solid rgba(255,255,255,0.1);
        display: flex; flex-direction: column; gap: 5px;
        backdrop-filter: blur(5px);
    }
    .footer-credits { font-size: 0.85rem; font-weight: 600; color: #d1d5db; }
    .footer-disclaimer { font-size: 0.7rem; opacity: 0.8; line-height: 1.3; }
    
    /* Ajuste para Mobile - Expander */
    .streamlit-expanderHeader {
        font-size: 0.9rem;
        font-weight: 600;
        color: #2563eb;
    }
    
    @media (prefers-color-scheme: light) {
        .result-card { background-color: #f0f9ff; border: 1px solid #bae6fd; }
        .snippet-box { background: #f1f5f9; color: #374151; border: 1px solid #e2e8f0; }
        .footer { background-color: rgba(255, 255, 255, 0.98); color: #4b5563; border-top: 1px solid #e5e7eb; }
        .footer-credits { color: #1f2937; }
    }
    </style>
""", unsafe_allow_html=True)

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

def search_local(term, data):
    results = []
    term_lower = term.lower()
    
    for doc in data:
        found_pages = []
        full_text_found = "" # Armazena o texto completo da primeira página achada
        snippet = ""
        
        try:
            pages = doc.get('pages_content', [])
            
            for page in pages:
                if term_lower in page['text'].lower():
                    page_num = str(page['number'])
                    found_pages.append(page_num)
                    
                    # Salva o texto completo da primeira ocorrência para exibir no mobile
                    if not full_text_found:
                        full_text_found = page['text']
                        
                    # Snippet curto para o card
                    if not snippet:
                        idx = page['text'].lower().find(term_lower)
                        start = max(0, idx - 40)
                        end = min(len(page['text']), idx + 100)
                        snippet = page['text'][start:end].replace("\n", " ")
            
            # Fallback Antigo
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

# --- HEADER ---
img_b64 = get_base64_image(LOGO_PATH)
if img_b64:
    st.markdown(f"""<div class="logo-container"><img src="data:image/png;base64,{img_b64}" width="150" style="border-radius:8px;"></div>""", unsafe_allow_html=True)
else:
    st.markdown("""<div class="logo-container"><h1 style='color:#0068c9;'>BT</h1></div>""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; margin-bottom:30px; margin-top:-10px;">
    <h1 style="font-weight:800; font-size:1.8rem; margin:0;">Buscador de Termos</h1>
    <p style="font-size:0.9rem; opacity:0.7; margin-top:5px;">Monitoramento Automatizado</p>
</div>
""", unsafe_allow_html=True)

# --- LÓGICA PRINCIPAL ---
data = load_data()

if data:
    last_update = data[0].get('scraped_at', 'Desconhecido')
    
    st.info(f"""
    📅 **Base atualizada em:** {last_update}
    \n📂 **Escopo da Pesquisa:** Monitorando as **{len(data)} últimas edições** (disponíveis na capa do portal DIOF).
    \n*O sistema não pesquisa no acervo histórico completo, apenas nos diários mais recentes.*
    """)
else:
    st.warning("⚠️ Base de dados vazia.")

query = st.text_input("O que você procura?", placeholder="Digite Nome, CPF, Matrícula...")


if query:
    if not data:
        st.error("Sem dados para pesquisar.")
    else:
        start_time = datetime.now()
        results = search_local(query, data)
        duration = (datetime.now() - start_time).total_seconds()
        
        if results:
            st.success(f"🔍 Encontrado em {len(results)} documentos ({duration:.3f}s)")
            
            for res in results:
                # 1. Definição do Link
                base_url = res['url'].strip()
                first_page = res['pages'][0] if res['pages'] else None
                
                # Link com página (Funciona no Desktop)
                if first_page and first_page != "9999" and first_page.isdigit():
                    pdf_link = f"{base_url}#page={first_page}"
                    btn_text = f"Abrir PDF na Pág. {first_page}"
                else:
                    pdf_link = base_url
                    btn_text = "Abrir PDF Original"

                # 2. Exibição das Páginas
                if "9999" in res['pages']:
                     pages_display = "Localizado no texto (Base antiga)"
                else:
                    pages_str = ', '.join(res['pages'])
                    if len(res['pages']) > 15: 
                        pages_str = f"{', '.join(res['pages'][:15])}..."
                    pages_display = f"Página(s): <strong>{pages_str}</strong>"

                # 3. Card HTML
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
                
                # 4. EXPANDER "MOBILE FRIENDLY" (Mostra o texto puro)
                # Se o usuário estiver no celular e o PDF não abrir na página certa,
                # ele pode ler o texto aqui mesmo.
                if res.get('full_text'):
                    with st.expander(f"📱 Visualizar Texto da Pág. {first_page}"):
                        st.text_area("Conteúdo extraído:", value=res['full_text'], height=300, disabled=True)
                        st.caption("Este é o texto exato extraído do PDF. Use para conferência rápida no celular.")

        else:
            st.warning(f"O termo **'{query}'** não foi encontrado.")