"""Módulo de busca inteligente no Notion para mods do The Sims 4."""

import re
from typing import Optional, List, Dict
from urllib.parse import urlparse, parse_qs
import logging

try:
    from notion_client import Client
except ImportError:
    Client = None

logger = logging.getLogger(__name__)


class NotionSearcher:
    """Busca inteligente de páginas de mods no Notion."""
    
    def __init__(self, api_key: str, database_id: str):
        """
        Inicializa o buscador Notion.
        
        Args:
            api_key: Notion API key
            database_id: ID da database do Notion
        """
        if Client is None:
            raise ImportError("notion-client não instalado. Instale com: pip install notion-client")
        
        self.client = Client(auth=api_key)
        self.database_id = database_id
        
    def extract_page_id_from_url(self, notion_url: str) -> Optional[str]:
        """
        Extrai o ID da página de uma URL do Notion.
        
        Args:
            notion_url: URL da página no Notion
            
        Returns:
            ID da página ou None se inválida
        """
        try:
            parsed = urlparse(notion_url)
            if 'notion.site' in parsed.netloc or parsed.netloc.endswith('.notion.site'):
                # Formato público: username.notion.site/page-title-pageid
                path_parts = parsed.path.strip('/').split('-')
                if len(path_parts) > 1:
                    potential_id = path_parts[-1]
                    if len(potential_id) == 32 and all(c in '0123456789abcdef' for c in potential_id):
                        return f"{potential_id[0:8]}-{potential_id[8:12]}-{potential_id[12:16]}-{potential_id[16:20]}-{potential_id[20:]}"
            
            # Formato padrão: app.notion.so/workspace/pageid?v=version
            path = parsed.path
            if path.startswith('/'):
                path = path[1:]
            
            parts = path.split('-')[-1] if '-' in path else path
            page_id = parts.split('?')[0] if '?' in parts else parts
            
            # Remove parâmetros se presentes
            if '?' in page_id:
                page_id = page_id.split('?')[0]
            
            # Valida formato UUID sem hifens
            if len(page_id) == 32 and all(c in '0123456789abcdefABCDEF' for c in page_id):
                # Formata com hifens
                return f"{page_id[0:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"
            
            # Query params fallback
            query_params = parse_qs(parsed.query)
            if 'p' in query_params:
                p_value = query_params['p'][0]
                if len(p_value) == 32:
                    return f"{p_value[0:8]}-{p_value[8:12]}-{p_value[12:16]}-{p_value[16:20]}-{p_value[20:]}"
            
            return None
        except Exception as e:
            logger.error(f"Erro ao extrair page_id: {e}")
            return None
    
    def normalize_url(self, url: str) -> str:
        """
        Normaliza a URL removendo protocolos, www e parâmetros.
        
        Args:
            url: URL original
            
        Returns:
            URL normalizada para busca
        """
        try:
            parsed = urlparse(url)
            scheme = f"{parsed.scheme}://" if parsed.scheme else ""
            netloc = parsed.netloc.lower().replace("www.", "")
            path = parsed.path.rstrip('/')
            
            # Remove parâmetros comuns de tracking
            query_params = parse_qs(parsed.query)
            clean_query = {k: v for k, v in query_params.items() if k not in ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'fbclid']}
            
            clean_query_str = '&'.join(f"{k}={v[0]}" for k, v in clean_query.items()) if clean_query else ""
            if clean_query_str:
                clean_query_str = f"?{clean_query_str}"
            
            return f"{scheme}{netloc}{path}{clean_query_str}"
        except Exception as e:
            logger.error(f"Erro ao normalizar URL {url}: {e}")
            return url
    
    def search_by_url(self, mod_url: str) -> Optional[str]:
        """
        Busca página por URL do mod (exata ou normalizada).
        
        Args:
            mod_url: URL do mod
            
        Returns:
            ID da página encontrada ou None
        """
        normalized_url = self.normalize_url(mod_url)
        
        try:
            # Busca exata
            response = self.client.data_sources.query(
                data_source_id=self.database_id,
                filter={
                    "or": [
                        {
                            "property": "Link",
                            "url": {
                                "equals": mod_url
                            }
                        },
                        {
                            "property": "Link",
                            "url": {
                                "equals": normalized_url
                            }
                        }
                    ]
                }
            )
            
            results = response.get('results', [])
            if results:
                return results[0]['id']
            
            # Busca contains se não encontrar exata
            response = self.client.data_sources.query(
                data_source_id=self.database_id,
                filter={
                    "property": "Link",
                    "url": {
                        "contains": normalized_url.split('?')[0]  # Sem params
                    }
                }
            )
            
            results = response.get('results', [])
            if results:
                return results[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Erro na busca por URL {mod_url}: {e}")
            return None
    
    def search_by_name_and_creator(self, name: str, creator: str = None) -> Optional[str]:
        """
        Busca página por nome do mod e criador (exato).
        
        Args:
            name: Nome do mod
            creator: Nome do criador (opcional)
            
        Returns:
            ID da página encontrada ou None
        """
        filter_obj = {
            "property": "Nome",
            "title": {
                "equals": name
            }
        }
        
        if creator:
            filter_obj = {
                "and": [
                    filter_obj,
                    {
                        "property": "Criador",
                        "rich_text": {
                            "equals": creator
                        }
                    }
                ]
            }
        
        try:
            response = self.client.data_sources.query(
                data_source_id=self.database_id,
                filter=filter_obj
            )
            
            results = response.get('results', [])
            if results:
                return results[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"Erro na busca por nome/criador: {e}")
            return None
    
    def fuzzy_search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Busca fuzzy para sugestões.
        
        Args:
            query: Termo de busca
            limit: Número máximo de resultados
            
        Returns:
            Lista de páginas encontradas
        """
        try:
            # Busca por nome
            response = self.client.data_sources.query(
                data_source_id=self.database_id,
                filter={
                    "property": "Nome",
                    "title": {
                        "contains": query
                    }
                },
                page_size=limit
            )
            
            results = []
            for page in response['results']:
                try:
                    # Extrai informações da página
                    properties = page['properties']
                    
                    name = ""
                    if 'Nome' in properties and properties['Nome']['title']:
                        name = properties['Nome']['title'][0]['plain_text']
                    
                    creator = ""
                    if 'Criador' in properties and properties['Criador']['rich_text']:
                        creator = properties['Criador']['rich_text'][0]['plain_text']
                    
                    url = ""
                    if 'Link' in properties and properties['Link']['url']:
                        url = properties['Link']['url']
                    
                    results.append({
                        'page_id': page['id'],
                        'name': name,
                        'creator': creator,
                        'url': url
                    })
                except Exception as inner_e:
                    logger.warning(f"Erro ao processar página individual: {inner_e}")
                    continue
            
            return results

        except Exception as e:
            logger.error(f"Erro na busca fuzzy por '{query}': {e}")
            return []
    
    def search(self, query: str) -> List[Dict]:
        """
        Busca inteligente que decide automaticamente o tipo de busca.
        
        Args:
            query: Pode ser URL, nome do mod ou criador
        
        Returns:
            Lista de resultados encontrados
        """
        # Se parece uma URL, tenta busca por URL
        if query.startswith('http://') or query.startswith('https://'):
            page_id = self.search_by_url(query)
            if page_id:
                # Busca detalhes da página encontrada
                try:
                    page = self.client.pages.retrieve(page_id)
                    properties = page['properties']
                    
                    name = ""
                    if 'Nome' in properties and properties['Nome']['title']:
                        name = properties['Nome']['title'][0]['plain_text']
                    
                    creator = ""
                    if 'Criador' in properties and properties['Criador']['rich_text']:
                        creator = properties['Criador']['rich_text'][0]['plain_text']
                    
                    url = ""
                    if 'Link' in properties and properties['Link']['url']:
                        url = properties['Link']['url']
                    
                    folder = ""
                    if 'Pasta' in properties and properties['Pasta']['select']:
                        folder = properties['Pasta']['select']['name']
                    
                    priority = ""
                    if 'Prioridade' in properties and properties['Prioridade']['select']:
                        priority = properties['Prioridade']['select']['name']
                    
                    return [{
                        'page_id': page_id,
                        'name': name,
                        'creator': creator,
                        'url': url,
                        'folder': folder,
                        'priority': priority
                    }]
                
                except Exception as e:
                    logger.error(f"Erro ao recuperar detalhes da página {page_id}: {str(e)}")
                    return []
        
        # Caso contrário, faz busca fuzzy por nome
        return self.fuzzy_search(query)
