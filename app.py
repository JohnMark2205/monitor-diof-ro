import streamlit as st
import json
import os
import base64
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Monitor DIOF-RO (Rápido)", page_icon="⚡", layout="centered")
DB_FILE = "dados.json"

# --- FUNÇÕES ---
def load_data():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def search_local(term, data):
    results = []
    term_lower = term.lower()
    
    for doc in data:
        # A "mágica" acontece aqui: buscamos no texto já salvo
        if term_lower in doc['content'].lower():
            # Encontrar onde está o termo (ex: extrair trecho)
            results.append(doc)
    return results

# --- INTERFACE ---
st.title("⚡ Buscador DIOF - Ultra Rápido")
st.caption(f"Pesquisa instantânea na base de dados processada.")

# Carregar dados
data = load_data()
if not data:
    st.warning("⚠️ Base de dados vazia. O robô ainda não rodou hoje.")
else:
    last_update = data[0].get('scraped_at', 'Desconhecido')
    st.info(f"📅 Última atualização da base: {last_update} | Documentos indexados: {len(data)}")

# Campo de Busca
query = st.text_input("O que você procura?", placeholder="Digite Nome, CPF, Matrícula...")

if query:
    if not data:
        st.error("Não há dados para pesquisar.")
    else:
        start = datetime.now()
        results = search_local(query, data)
        duration = (datetime.now() - start).total_seconds()
        
        st.success(f"🔍 Encontrado em {len(results)} documentos ({duration:.4f} segundos)")
        
        for res in results:
            with st.expander(f"📄 {res['title']}"):
                st.write(f"**Indexado em:** {res['scraped_at']}")
                st.markdown(f"[🔗 Baixar/Visualizar PDF Original]({res['url']})")
                
                # Snippet (mostra um pedaço do texto onde achou)
                content_lower = res['content'].lower()
                idx = content_lower.find(query.lower())
                if idx != -1:
                    start_snip = max(0, idx - 50)
                    end_snip = min(len(res['content']), idx + 100)
                    snippet = res['content'][start_snip:end_snip].replace("\n", " ")
                    st.code(f"...{snippet}...", language="text")