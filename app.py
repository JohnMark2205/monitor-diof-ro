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

# Caminho do Banco de Dados
DB_FILE = "dados.json"

# --- CSS E ESTILOS VISUAIS ---
st.markdown("""
    <style>
    /* Ajuste de espaçamento para o conteúdo não ficar escondido atrás do rodapé */
    .block-container { 
        padding-top: 3rem; 
        padding-bottom: 8rem; /* Espaço extra para o rodapé */
    }
    
    /* Centralizar Logo */
    .logo-container {
        display: flex; justify-content: center; align-items: center; width: 100%; margin-bottom: 20px;
    }
    
    /* Cards de Resultado */
    .result-card {
        background-color: rgba(37, 99, 235, 0.05); 
        border: 1px solid rgba(37, 99, 235, 0.2);
        padding: 15px; border-radius: 10px; margin-bottom: 10px; 
        border-left: 5px solid #2563eb;
    }
    
    /* Snippet de texto (trecho encontrado) */
    .snippet-box {
        background: rgba(0,0,0,0.2); 
        padding: 8px; 
        border-radius: 5px; 
        font-family: monospace; 
        font-size: 0.85rem; 
        margin-bottom: 8px;
        color: #e5e7eb;
    }
    
    /* RODAPÉ FIXO (Configuração Robusta) */
    .footer {
        position: fixed; 
        left: 0; 
        bottom: 0; 
        width: 100%;
        background-color: rgba(14, 17, 23, 0.98); /* Quase 100% opaco */
        color: #9ca3af;
        text-align: center; 
        padding: 15px 20px; 
        z-index: 99999; /* Garante que fique na frente de tudo */
        border-top: 1px solid rgba(255,255,255,0.1);
        display: flex; 
        flex-direction: column; 
        gap: 5px;
        backdrop-filter: blur(5px);
    }
    .footer-credits { font-size: 0.85rem; font-weight: 600; color: #d1d5db; }
    .footer-disclaimer { font-size: 0.7rem; opacity: 0.8; line-height: 1.3; }
    
    /* Adaptação para Modo Claro (Light Mode) */
    @media (prefers-color-scheme: light) {
        .result-card { background-color: #f0f9ff; border: 1px solid #bae6fd; }
        .snippet-box { background: #f1f5f9; color: #374151; }
        .footer { background-color: rgba(255, 255, 255, 0.98); color: #4b5563; border-top: 1px solid #e5e7eb; }
        .footer-credits { color: #1f2937; }
    }
    </style>
""", unsafe_allow_html=True)

# --- RENDERIZAÇÃO IMEDIATA DO RODAPÉ ---
# Colocamos aqui no topo para garantir que carregue sempre
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
    """Converte a imagem da logo para Base64 para exibição segura"""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def load_data():
    """Carrega o JSON gerado pelo robô"""
    if not os.path.exists(DB_FILE): return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except: return []

def search_local(term, data):
    """Busca ultra-rápida no JSON local"""
    results = []
    term_lower = term.lower()
    
    for doc in data:
        found_pages = []
        snippet = ""
        
        try:
            # Verifica se o JSON tem a estrutura nova (com páginas)
            pages = doc.get('pages_content', [])
            
            # Se for estrutura antiga (apenas 'content'), adapta
            if not pages and 'content' in doc:
                if term_lower in doc['content'].lower():
                    found_pages.append("Ver no PDF")
                    idx = doc['content'].lower().find(term_lower)
                    snippet = doc['content'][idx:idx+100]
            
            # Estrutura nova (Página a Página)
            for page in pages:
                if term_lower in page['text'].lower():
                    found_pages.append(str(page['number']))
                    # Pega o snippet da primeira ocorrência
                    if not snippet:
                        idx = page['text'].lower().find(term_lower)
                        start = max(0, idx - 40)
                        end = min(len(page['text']), idx + 100)
                        snippet = page['text'][start:end].replace("\n", " ")
        except:
            continue
            
        if found_pages:
            results.append({
                "title": doc['title'],
                "url": doc['url'],
                "date": doc.get('scraped_at', 'Data desc.'),
                "pages": found_pages,
                "snippet": snippet
            })
    return results

# --- CABEÇALHO (LOGO) ---
logo_path = "logo_diof.png"
img_b64 = get_base64_image(logo_path)

if img_b64:
    # Renderiza Logo Centralizada
    st.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{img_b64}" width="150" style="border-radius:8px;">
        </div>
    """, unsafe_allow_html=True)
else:
    # Fallback se não tiver imagem
    st.markdown("""<div class="logo-container"><h1 style='color:#0068c9;'>BT</h1></div>""", unsafe_allow_html=True)

st.markdown("""
    <div style="text-align:center; margin-bottom:30px; margin-top:-10px;">
        <h1 style="font-weight:800; font-size:1.8rem; margin:0;">Buscador de Termos</h1>
        <p style="font-size:0.9rem; opacity:0.7; margin-top:5px;">Monitoramento Automatizado</p>
    </div>
""", unsafe_allow_html=True)

# --- LÓGICA PRINCIPAL ---
data = load_data()

# Exibe informações sobre a base de dados
if data:
    last_update = data[0].get('scraped_at', 'Desconhecido')
    st.info(f"📅 Base atualizada em: **{last_update}** | {len(data)} documentos indexados.")
else:
    st.warning("⚠️ Base de dados vazia. Aguardando a execução automática do robô.")

# Campo de Busca
query = st.text_input("O que você procura?", placeholder="Digite Nome, CPF, Matrícula...")

if query:
    if not data:
        st.error("Não há dados carregados para realizar a pesquisa.")
    else:
        start_time = datetime.now()
        results = search_local(query, data)
        duration = (datetime.now() - start_time).total_seconds()
        
        if results:
            st.success(f"🔍 Encontrado em {len(results)} documentos ({duration:.3f}s)")
            
            for res in results:
                # Formatação das páginas
                pages_str = ', '.join(res['pages'])
                if len(res['pages']) > 10: 
                    pages_str = f"{', '.join(res['pages'][:10])}..."
                
                st.markdown(f"""
                <div class="result-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0; font-size:1.1rem; color:#2563eb;">📄 {res['title']}</h3>
                        <span style="font-size:0.75rem; color:#6b7280;">{res['date']}</span>
                    </div>
                    
                    <p style="margin:8px 0; font-size:0.95rem;">
                        ✅ Páginas encontradas: <strong>{pages_str}</strong>
                    </p>
                    
                    <div class="snippet-box">
                        ...{res['snippet']}...
                    </div>
                    
                    <a href="{res['url']}" target="_blank" style="text-decoration:none; color:#2563eb; font-weight:bold; font-size:0.9rem;">
                        ⬇️ Abrir PDF Original
                    </a>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"O termo **'{query}'** não foi encontrado nos documentos indexados hoje.")