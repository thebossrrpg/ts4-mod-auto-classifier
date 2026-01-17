"""TS4 Mod Auto-Classifier - Aplicação Streamlit"""

import streamlit as st
import os
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
    
            # Carrega credenciais dos secrets (fixas)
    notion_api_key = st.secrets["NOTION_API_KEY"]   
    database_id = st.secrets["NOTION_DB_ID"]
    if notion_api_key and database_id:
        st.success("✅ Configurado")
    else:
        st.warning("⚠️ Configure as credenciais")

# Tabs principais
tab1, tab2, tab3 = st.tabs(["🔍 Buscar no Notion", "🆕 Novo Mod", "📋 Classificar em Lote"])

# Tab 1: Buscar no Notion
with tab1:
    st.header("Buscar Mods no Notion")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Digite URL, nome ou criador do mod",
            placeholder="https://modthesims.info/..."
        )
    
    with col2:
        search_button = st.button("🔍 Buscar", type="primary", use_container_width=True)
    
    if search_button and search_query:
        if not (notion_api_key and database_id):
            st.error("Por favor, configure as credenciais do Notion na sidebar")
        else:
            with st.spinner("Buscando no Notion..."):
                try:
                    searcher = NotionSearcher(notion_api_key, database_id)
                    results = searcher.search(search_query)
                    
                    if results:
                        st.success(f"Encontrados {len(results)} resultado(s)")
                        
                        for result in results:
                            with st.expander(f"📄 {result.get('name', 'Sem nome')}"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**Criador:**", result.get('creator', 'N/A'))
                                    st.write("**Pasta:**", result.get('folder', 'N/A'))
                                
                                with col2:
                                    st.write("**Prioridade:**", result.get('priority', 'N/A'))
                                    if result.get('url'):
                                        st.link_button("🔗 Ver Página", result['url'])
                    else:
                        st.info("Nenhum resultado encontrado")
                        
                except Exception as e:
                    st.error(f"Erro ao buscar: {str(e)}")

# Tab 2: Novo Mod
with tab2:
    st.header("Adicionar Novo Mod")
    
    mod_url = st.text_input(
        "URL do Mod",
        placeholder="https://modthesims.info/d/123456",
        help="Cole a URL da página do mod"
    )
    
    if st.button("🤖 Extrair e Classificar", type="primary"):
        if not mod_url:
            st.warning("Por favor, insira uma URL")
        elif not (notion_api_key and database_id):
            st.error("Configure as credenciais do Notion na sidebar")
        else:
            # Extração
            with st.spinner("Extraindo informações da página..."):
                try:
                    extractor = ModExtractor()
                    mod_info = extractor.extract_from_url(mod_url)
                    
                    st.success("✅ Informações extraídas!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Nome:**", mod_info.get('name', 'Não encontrado'))
                        st.write("**Criador:**", mod_info.get('creator', 'Não encontrado'))
                    with col2:
                        st.write("**URL:**", mod_info.get('url'))
                    
                    st.write("**Descrição:**", mod_info.get('description', 'Não encontrada')[:200] + "...")
                    
                except Exception as e:
                    st.error(f"Erro na extração: {str(e)}")
                    mod_info = None
            
            # Classificação
            if mod_info and mod_info.get('name'):
                with st.spinner("Classificando mod..."):
                    try:
                        classifier = ModClassifier()
                        classification = classifier.classify_mod(
                            mod_info.get('name', ''),
                            mod_info.get('description', ''),
                            mod_info.get('creator', '')
                        )
                        
                        st.success("✅ Mod classificado!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Prioridade", classification['priority'])
                        with col2:
                            st.metric("Confiança", f"{classification['confidence']*100:.0f}%")
                        with col3:
                            st.info(f"📁 {classification['folder']}")
                        
                        # Salvar no Notion
                        st.markdown("---")
                        if st.button("💾 Salvar no Notion", type="primary"):
                            with st.spinner("Salvando..."):
                                try:
                                    client = NotionClient(notion_api_key, database_id)
                                    
                                    page_data = {
                                        'name': mod_info['name'],
                                        'url': mod_info['url'],
                                        'creator': mod_info.get('creator', ''),
                                        'priority': classification['priority'],
                                        'folder': classification['folder'],
                                        'notes': f"Confiança: {classification['confidence']*100:.0f}%"
                                    }
                                    
                                    result = client.create_page(page_data)
                                    st.success("✅ Mod salvo no Notion com sucesso!")
                                    
                                except Exception as e:
                                    st.error(f"Erro ao salvar: {str(e)}")
                        
                    except Exception as e:
                        st.error(f"Erro na classificação: {str(e)}")

# Tab 3: Classificar em Lote
with tab3:
    st.header("Classificação em Lote")
    
    st.markdown("""
    Cole uma lista de URLs de mods (uma por linha) para classificar múltiplos mods de uma vez.
    """)
    
    urls_text = st.text_area(
        "URLs dos Mods",
        height=200,
        placeholder="https://modthesims.info/d/123456\nhttps://modthesims.info/d/789012\n..."
    )
    
    if st.button("🚀 Processar em Lote", type="primary"):
        if not urls_text.strip():
            st.warning("Por favor, insira pelo menos uma URL")
        elif not (notion_api_key and database_id):
            st.error("Configure as credenciais do Notion na sidebar")
        else:
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
            
            st.info(f"Processando {len(urls)} URLs...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            extractor = ModExtractor()
            classifier = ModClassifier()
            client = NotionClient(notion_api_key, database_id)
            
            results = []
            for i, url in enumerate(urls):
                status_text.text(f"Processando {i+1}/{len(urls)}: {url[:50]}...")
                
                try:
                    # Extrai
                    mod_info = extractor.extract_from_url(url)
                    
                    # Classifica
                    if mod_info.get('name'):
                        classification = classifier.classify_mod(
                            mod_info['name'],
                            mod_info.get('description', ''),
                            mod_info.get('creator', '')
                        )
                        
                        results.append({
                            'url': url,
                            'name': mod_info['name'],
                            'status': '✅ Sucesso',
                            'folder': classification['folder'],
                            'priority': classification['priority']
                        })
                    else:
                        results.append({
                            'url': url,
                            'name': 'N/A',
                            'status': '⚠️ Sem nome',
                            'folder': 'N/A',
                            'priority': 'N/A'
                        })
                        
                except Exception as e:
                    results.append({
                        'url': url,
                        'name': 'N/A',
                        'status': f'❌ Erro: {str(e)[:30]}',
                        'folder': 'N/A',
                        'priority': 'N/A'
                    })
                
                progress_bar.progress((i + 1) / len(urls))
            
            status_text.text("✅ Processamento concluído!")
            
            # Mostra resultados
            st.markdown("### 📊 Resultados")
            st.dataframe(results, use_container_width=True)
            
            # Opção de salvar todos
            if st.button("💾 Salvar Todos no Notion"):
                saved = 0
                for result in results:
                    if result['status'] == '✅ Sucesso':
                        try:
                            page_data = {
                                'name': result['name'],
                                'url': result['url'],
                                'priority': result['priority'],
                                'folder': result['folder']
                            }
                            client.create_page(page_data)
                            saved += 1
                        except:
                            pass
                
                st.success(f"✅ {saved} mods salvos no Notion!")

# Footer
st.markdown("---")
st.markdown("Made with ❤️ for The Sims 4 Community")
