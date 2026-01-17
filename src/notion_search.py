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
        Extrai o page_id de uma URL do Notion.
        
        Args:
            notion_url: URL da página do Notion
            
        Returns:
            Page ID ou None
            
        Examples:
            >>> extract_page_id_from_url("https://notion.so/Page-Name-abc123def456")
            'abc123def456'
        """
        try:
            # Pattern para URLs do Notion: última parte após o último hífen
            # https://notion.so/workspace/Page-Name-abc123def456
            # https://www.notion.so/Page-Name-abc123def456?pvs=4
            
            parsed = urlparse(notion_url)
            path = parsed.path.rstrip('/')
            
            # Remove query params se houver
            if '?' in path:
                path = path.split('?')[0]
            
            # Pega a última parte do path
            page_segment = path.split('/')[-1]
            
            # O ID é a última parte após o último hífen
            # Formato: Page-Name-abc123def456
            if '-' in page_segment:
                page_id = page_segment.split('-')[-1]
                # Remove hífens do ID (Notion aceita com ou sem)
                page_id = page_id.replace('-', '')
                
                # Valida se é um ID válido (32 caracteres hex)
                if len(page_id) == 32 and all(c in '0123456789abcdefABCDEF' for c in page_id):
                    return page_id
            
            logger.warning(f"Não foi possível extrair page_id de: {notion_url}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao extrair page_id: {e}")
            return None
    
    def normalize_url(self, url: str) -> str:
        """
        Normaliza URL do mod removendo query parameters.
        
        Args:
            url: URL do mod
            
        Returns:
            URL normalizada
        """
        try:
            parsed = urlparse(url)
            # Remove query params e fragment
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            return normalized.rstrip('/')
        except:
            return url.rstrip('/')
    
    def search_by_url(self, mod_url: str) -> Optional[str]:
        """
        Busca página do Notion pela URL do mod.
        
        Args:
            mod_url: URL do mod (ex: https://modthesims.info/d/12345)
            
        Returns:
            Page ID se encontrado, None caso contrário
        """
        try:
            normalized_url = self.normalize_url(mod_url)
            
            # Busca exata por URL
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Link",
                    "url": {
                        "equals": normalized_url
                    }
                }
            )
            
            if response['results']:
                page_id = response['results'][0]['id']
                logger.info(f"Página encontrada por URL: {page_id}")
                return page_id
            
            # Se não encontrou, tenta busca parcial
            # (útil se a URL foi salva com query params)
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Link",
                    "url": {
                        "contains": mod_url.split('?')[0].split('/')[-1]
                    }
                }
            )
            
            if response['results']:
                page_id = response['results'][0]['id']
                logger.info(f"Página encontrada por busca parcial: {page_id}")
                return page_id
            
            logger.info(f"Nenhuma página encontrada para URL: {mod_url}")
            return None
            
        except Exception as e:
            logger.error(f"Erro na busca por URL: {e}")
            return None
    
    def search_by_name_and_creator(self, name: str, creator: str = None) -> Optional[str]:
        """
        Busca página do Notion por nome do mod e criador.
        
        Args:
            name: Nome do mod
            creator: Nome do criador (opcional)
            
        Returns:
            Page ID se encontrado, None caso contrário
        """
        try:
            filters = []
            
            # Filtro por nome
            if name:
                filters.append({
                    "property": "Nome",
                    "title": {
                        "contains": name
                    }
                })
            
            # Filtro por criador
            if creator:
                filters.append({
                    "property": "Criador",
                    "rich_text": {
                        "contains": creator
                    }
                })
            
            # Monta query
            query_filter = None
            if len(filters) == 1:
                query_filter = filters[0]
            elif len(filters) > 1:
                query_filter = {
                    "and": filters
                }
            
            if not query_filter:
                logger.warning("Busca sem filtros")
                return None
            
            response = self.client.databases.query(
                database_id=self.database_id,
                filter=query_filter
            )
            
            if response['results']:
                page_id = response['results'][0]['id']
                logger.info(f"Página encontrada por nome/criador: {page_id}")
                return page_id
            
            logger.info(f"Nenhuma página encontrada para: {name} / {creator}")
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
            response = self.client.databases.query(
                database_id=self.database_id,
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
                except Exception as e:
                    logger.warning(f"Erro ao processar página: {e}")
                    continue
            
            return results

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
                    logger.error(f"Erro ao buscar detalhes da página: {e}")
                    return []
        
        # Caso contrário, faz busca fuzzy por nome
        return self.fuzzy_search(query)
            
