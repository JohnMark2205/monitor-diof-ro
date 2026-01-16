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

DB_FILE = "dados.json"

# --- CSS E ESTILOS VISUAIS ---
st.markdown("""
    <style>
    /* Layout Mobile */
    .block-container { 
        padding-top: 2rem; 
        padding-bottom: 8rem; 
    }
    
    .logo-container {
        display: flex; justify-content: center; align-items: center; width: 100%; margin-bottom: 20px;
    }
    
    /* Card de Resultado */
    .result-card {
        background-color: rgba(37, 99, 235, 0.05); 
        border: 1px solid rgba(37, 99, 235, 0.2);
        padding: 16px; 
        border-radius: 12px; 
        margin-bottom: 16px; 
        border-left: 5px solid #2563eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Snippet (Trecho do texto) */
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
    
    /* BOTÃO CLEAN */
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
    
    /* Efeito Hover */
    .pdf-button:hover {
        background-color: #1d4ed8;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(37, 99, 235, 0.3);
    }
    .pdf-button:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.2);
    }
    
    /* RODAPÉ FIXO */
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
        snippet = ""
        
        try:
            pages = doc.get('pages_content', [])
            
            # 1. Procura nas páginas (Novo formato)
            for page in pages:
                if term_lower in page['text'].lower():
                    found_pages.append(str(page['number']))
                    if not snippet:
                        idx = page['text'].lower().find(term_lower)
                        start = max(0, idx - 40)
                        end = min(len(page['text']), idx + 100)
                        snippet = page['text'][start:end].replace("\n", " ")
            
            # 2. Fallback (Formato antigo)
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
                "snippet": snippet
            })
    return results

# --- HEADER ---
logo_path = "logo_diof.png"
img_b64 = get_base64_image(logo_path)

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

# --- LÓGICA ---
data = load_data()

if data:
    last_update = data[0].get('scraped_at', 'Desconhecido')
    st.info(f"📅 Base atualizada em: **{last_update}** | {len(data)} documentos indexados.")
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
                # TRATAMENTO DO LINK DA PÁGINA
                # Se tiver número de página válido, adiciona #page=X ao link
                pdf_link = res['url']
                first_page = res['pages'][0] if res['pages'] else None
                
                if first_page and first_page != "9999" and first_page.isdigit():
                    pdf_link = f"{res['url']}#page={first_page}"

                # Exibição do texto das páginas
                if "9999" in res['pages']:
                     pages_display = "Página: Não identificada (Necessário limpar base antiga)"
                else:
                    pages_str = ', '.join(res['pages'])
                    if len(res['pages']) > 15: 
                        pages_str = f"{', '.join(res['pages'][:15])}..."
                    pages_display = f"Página(s): <strong>{pages_str}</strong>"

                # HTML DO CARD
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
Abrir no local do PDF
</a>
</div>
"""
                st.markdown(html_card, unsafe_allow_html=True)
        else:
            st.warning(f"O termo **'{query}'** não foi encontrado.")