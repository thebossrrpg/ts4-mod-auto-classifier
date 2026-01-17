"""Extrator de conteúdo de páginas de mods."""

import logging
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class ModExtractor:
    """Extrai informações de páginas de mods."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_from_url(self, url: str) -> Dict[str, str]:
        """
        Extrai informações de uma URL de mod.
        
        Args:
            url: URL da página do mod
            
        Returns:
            Dicionário com nome, descrição e criador
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrai informações
            mod_info = {
                'url': url,
                'name': self._extract_title(soup),
                'description': self._extract_description(soup),
                'creator': self._extract_creator(soup)
            }
            
            logger.info(f"Conteúdo extraído de: {url}")
            return mod_info
            
        except Exception as e:
            logger.error(f"Erro ao extrair de {url}: {e}")
            return {
                'url': url,
                'name': '',
                'description': '',
                'creator': ''
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrai título da página."""
        # Tenta várias estratégias
        title_tags = [
            soup.find('h1'),
            soup.find('title'),
            soup.find(class_=re.compile('title|heading', re.I))
        ]
        
        for tag in title_tags:
            if tag:
                text = tag.get_text(strip=True)
                if text:
                    return text
        
        return ''
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extrai descrição do mod."""
        # Tenta meta description primeiro
        meta = soup.find('meta', {'name': 'description'}) or \
               soup.find('meta', {'property': 'og:description'})
        
        if meta and meta.get('content'):
            return meta.get('content')
        
        # Tenta parágrafo principal
        paragraphs = soup.find_all('p', limit=3)
        if paragraphs:
            texts = [p.get_text(strip=True) for p in paragraphs]
            return ' '.join(texts)[:500]  # Limita tamanho
        
        return ''
    
    def _extract_creator(self, soup: BeautifulSoup) -> str:
        """Extrai nome do criador."""
        # Tenta várias estratégias
        creator_patterns = [
            soup.find(class_=re.compile('author|creator', re.I)),
            soup.find('a', {'rel': 'author'}),
            soup.find(string=re.compile(r'by\s+', re.I))
        ]
        
        for element in creator_patterns:
            if element:
                if hasattr(element, 'get_text'):
                    text = element.get_text(strip=True)
                else:
                    text = str(element)
                
                # Limpa texto
                text = re.sub(r'by\s+', '', text, flags=re.I).strip()
                if text:
                    return text
        
        return ''
    
    def extract_batch(self, urls: list) -> list:
        """
        Extrai informações de múltiplas URLs.
        
        Args:
            urls: Lista de URLs
            
        Returns:
            Lista de dicionários com informações
        """
        results = []
        for url in urls:
            mod_info = self.extract_from_url(url)
            results.append(mod_info)
        
        logger.info(f"Extraídos {len(results)} mods em lote")
        return results
