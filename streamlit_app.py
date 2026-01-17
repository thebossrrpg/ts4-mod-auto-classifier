"""TS4 Mod Auto-Classifier - Aplicação Streamlit"""

import streamlit as st
from src.notion_search import NotionSearcher
from src.notion_client import NotionClient
from src.mod_classifier import ModClassifier
from src.mod_extractor import ModExtractor

# Configuração da página
st.set_page_config(
    page_title="TS4 Mod Auto-Classifier",
    page_icon="🎮",
    layout="wide"
)

# Título
st.title("🎮 TS4 Mod Auto-Classifier")
st.markdown("Sistema completo de classificação automática de mods do The Sims 4")

# Sidebar com configurações
with st.sidebar:
    st.header("⚙️ Configurações")

    # Carrega credenciais dos secrets
    notion_api_key = st.secrets.get("NOTION_API_KEY")
    database_id = st.secrets.get("NOTION_DB_ID")

    if notion_api_key and database_id:
        st.success("✅ Configurado")
    else:
        st.warning("⚠️ Configure as credenciais")

# Tabs principais
tab1, tab2, tab3 = st.tabs(
    ["🔍 Buscar no Notion", "🆕 Novo Mod", "📋 Classificar em Lote"]
)

# ---------------- TAB 1 ----------------
with tab1:
    st.header("Buscar Mods no Notion")

    col1, col2 = st.columns([3, 1])

    with col1:
        search_query = st.text_input(
            "Digite URL, nome ou criador do mod",
            placeholder="https://modthesims.info/..."
        )

    with col2:
        search_button = st.button(
            "🔍 Buscar", type="primary", use_container_width=True
        )

    if search_button and search_query:
        if not (notion_api_key and database_id):
            st.error("Configure as credenciais do Notion na sidebar")
        else:
            with st.spinner("Buscando no Notion..."):
                try:
                    searcher = NotionSearcher(notion_api_key, database_id)
                    results = searcher.search(search_query)

                    if results:
                        st.success(f"Encontrados {len(results)} resultado(s)")
                        for result in results:
                            with st.expander(f"📄 {result.get('name', 'Sem nome')}"):
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.write("**Criador:**", result.get("creator", "N/A"))
                                    st.write("**Pasta:**", result.get("folder", "N/A"))
                                with c2:
                                    st.write("**Prioridade:**", result.get("priority", "N/A"))
                                    if result.get("url"):
                                        st.link_button("🔗 Ver Página", result["url"])
                    else:
                        st.info("Nenhum resultado encontrado")

                except Exception as e:
                    st.error(f"Erro ao buscar: {e}")

# ---------------- TAB 2 ----------------
with tab2:
    st.header("Adicionar Novo Mod")

    mod_url = st.text_input(
        "URL do Mod",
        placeholder="https://modthesims.info/d/123456",
    )

    if st.button("🤖 Extrair e Classificar", type="primary"):
        if not mod_url:
            st.warning("Por favor, insira uma URL")
        elif not (notion_api_key and database_id):
            st.error("Configure as credenciais do Notion")
        else:
            with st.spinner("Extraindo informações..."):
                try:
                    extractor = ModExtractor()
                    mod_info = extractor.extract_from_url(mod_url)
                except Exception as e:
                    st.error(f"Erro na extração: {e}")
                    mod_info = None

            if mod_info and mod_info.get("name"):
                st.success("✅ Informações extraídas!")

                st.write("**Nome:**", mod_info.get("name"))
                st.write("**Criador:**", mod_info.get("creator", "N/A"))
                st.write("**URL:**", mod_info.get("url"))

                with st.spinner("Classificando mod..."):
                    try:
                        classifier = ModClassifier()
                        classification = classifier.classify_mod(
                            mod_info["name"],
                            mod_info.get("description", ""),
                            mod_info.get("creator", "")
                        )

                        st.success("✅ Mod classificado!")
                        st.metric("Prioridade", classification["priority"])
                        st.metric(
                            "Confiança",
                            f"{classification['confidence']*100:.0f}%"
                        )
                        st.info(f"📁 {classification['folder']}")

                        if st.button("💾 Salvar no Notion", type="primary"):
                            with st.spinner("Salvando..."):
                                try:
                                    searcher = NotionSearcher(
                                        notion_api_key, database_id
                                    )

                                    if searcher.search_by_url(mod_info["url"]):
                                        st.warning("⚠️ Esse mod já existe no Notion.")
                                        st.stop()

                                    client = NotionClient(
                                        notion_api_key, database_id
                                    )

                                    client.create_page({
                                        "name": mod_info["name"],
                                        "url": mod_info["url"],
                                        "creator": mod_info.get("creator", ""),
                                        "priority": classification["priority"],
                                        "folder": classification["folder"],
                                    })

                                    st.success("✅ Mod salvo com sucesso!")

                                except Exception as e:
                                    st.error(f"Erro ao salvar: {e}")

                    except Exception as e:
                        st.error(f"Erro na classificação: {e}")

# ---------------- TAB 3 ----------------
with tab3:
    st.header("Classificação em Lote")

    urls_text = st.text_area(
        "URLs dos Mods",
        height=200,
        placeholder="https://modthesims.info/d/123456"
    )

    if st.button("🚀 Processar em Lote", type="primary"):
        if not urls_text.strip():
            st.warning("Insira pelo menos uma URL")
        else:
            urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
            extractor = ModExtractor()
            classifier = ModClassifier()
            client = NotionClient(notion_api_key, database_id)

            results = []

            for url in urls:
                try:
                    mod_info = extractor.extract_from_url(url)
                    if mod_info.get("name"):
                        classification = classifier.classify_mod(
                            mod_info["name"],
                            mod_info.get("description", ""),
                            mod_info.get("creator", "")
                        )
                        client.create_page({
                            "name": mod_info["name"],
                            "url": url,
                            "priority": classification["priority"],
                            "folder": classification["folder"],
                        })
                        results.append({"URL": url, "Status": "✅ Sucesso"})
                except Exception as e:
                    results.append({"URL": url, "Status": f"❌ {e}"})

            st.dataframe(results)

# Footer
st.markdown("---")
st.markdown("Made with ❤️ for The Sims 4 Community")
