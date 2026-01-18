"""
Busca inteligente no Notion para mods do The Sims 4.
Responsável APENAS por leitura/busca.
"""

import logging
from typing import Optional, List, Dict
from urllib.parse import urlparse

from notion_client import Client

logger = logging.getLogger(__name__)


class NotionSearcher:
    """Busca inteligente de páginas no Notion."""

    def __init__(self, api_key: str, database_id: str):
        self.client = Client(auth=api_key)
        self.database_id = database_id

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def normalize_url(self, url: str) -> str:
        """
        Normaliza URL para comparação consistente no Notion.
        """
        parsed = urlparse(url)
        netloc = parsed.netloc.lower().replace("www.", "")
        path = parsed.path.rstrip("/")
        return f"{netloc}{path}"

    def _safe_title(self, prop: Dict) -> str:
        try:
            return prop["title"][0]["plain_text"]
        except Exception:
            return ""

    def _safe_rich_text(self, prop: Dict) -> str:
        try:
            return prop["rich_text"][0]["plain_text"]
        except Exception:
            return ""

    def _safe_select(self, prop: Dict) -> Optional[str]:
        try:
            return prop["select"]["name"]
        except Exception:
            return None

    # --------------------------------------------------
    # Searches
    # --------------------------------------------------

    def search_by_url(self, mod_url: str) -> Optional[str]:
        """
        Busca exata por URL normalizada.
        Retorna page_id se existir, senão None.
        """
        normalized = self.normalize_url(mod_url)

        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Link",
                    "url": {"contains": normalized}
                }
            )

            results = response.get("results", [])
            if results:
                return results[0]["id"]

            return None

        except Exception as e:
            logger.exception("Erro na busca por URL")
            return None

    def fuzzy_search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Busca aproximada por Nome.
        """
        try:
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Nome",
                    "title": {"contains": query}
                },
                page_size=limit
            )

            results = []
            for page in response.get("results", []):
                props = page.get("properties", {})

                results.append({
                    "page_id": page.get("id"),
                    "name": self._safe_title(props.get("Nome", {})),
                    "creator": self._safe_rich_text(props.get("Criador", {})),
                    "url": props.get("Link", {}).get("url"),
                    "folder": self._safe_select(props.get("Pasta", {})),
                    "priority": self._safe_select(props.get("Prioridade", {})),
                })

            return results

        except Exception as e:
            logger.exception("Erro na busca fuzzy")
            return []

    def search(self, query: str) -> List[Dict]:
        """
        Busca principal:
        - URL → busca direta
        - Texto → fuzzy search
        """
        # ---------------- URL ----------------
        if query.startswith("http"):
            page_id = self.search_by_url(query)
            if not page_id:
                return []

            try:
                page = self.client.pages.retrieve(page_id)
                props = page.get("properties", {})

                return [{
                    "page_id": page_id,
                    "name": self._safe_title(props.get("Nome", {})),
                    "creator": self._safe_rich_text(props.get("Criador", {})),
                    "url": props.get("Link", {}).get("url"),
                    "folder": self._safe_select(props.get("Pasta", {})),
                    "priority": self._safe_select(props.get("Prioridade", {})),
                }]

            except Exception as e:
                logger.exception("Erro ao recuperar página por URL")
                return []

        # ---------------- Texto ----------------
        return self.fuzzy_search(query)
