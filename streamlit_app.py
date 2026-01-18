import streamlit as st

from notion_search import NotionSearcher
from notion_db_client import NotionClient
from mod_classifier import ModClassifier
from mod_extractor import ModExtractor

st.set_page_config(
    page_title="TS4 Mod Auto-Classifier",
    page_icon="🎮",
    layout="wide"
)

st.title("🎮 TS4 Mod Auto-Classifier")

with st.sidebar:
    st.header("⚙️ Configurações")
    notion_api_key = st.secrets.get("NOTION_API_KEY")
    database_id = st.secrets.get("NOTION_DB_ID")

    if notion_api_key and database_id:
        st.success("✅ Configurado")
    else:
        st.warning("⚠️ Configure as credenciais")

tab1, tab2 = st.tabs(["🔍 Buscar", "🆕 Novo Mod"])

# ---------------- TAB 1 ----------------
with tab1:
    query = st.text_input("Buscar por nome ou URL")

    if st.button("Buscar"):
        searcher = NotionSearcher(notion_api_key, database_id)
        results = searcher.search(query)

        if not results:
            st.info("Nenhum resultado encontrado")

        for r in results:
            with st.expander(r["name"] or "Sem nome"):
                st.write("Criador:", r["creator"])
                st.write("Pasta:", r["folder"])
                st.write("Prioridade:", r["priority"])
                if r["url"]:
                    st.link_button("Abrir", r["url"])

# ---------------- TAB 2 ----------------
with tab2:
    url = st.text_input("URL do mod")

    if st.button("Extrair e salvar"):
        extractor = ModExtractor()
        mod = extractor.extract_from_url(url)

        classifier = ModClassifier()
        classification = classifier.classify_mod(
            mod["name"],
            mod.get("description", ""),
            mod.get("creator", "")
        )

        client = NotionClient(notion_api_key, database_id)
        searcher = NotionSearcher(notion_api_key, database_id)

        if searcher.search_by_url(url):
            st.warning("Já existe no Notion")
        else:
            client.create_page({
                "name": mod["name"],
                "url": url,
                "creator": mod.get("creator", ""),
                "priority": classification["priority"],
                "folder": classification["folder"],
            })
            st.success("Salvo com sucesso")
