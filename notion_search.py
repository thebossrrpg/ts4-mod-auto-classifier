"""
Busca inteligente no Notion para mods do The Sims 4.
"""

import logging
from typing import Optional, List, Dict
from urllib.parse import urlparse, parse_qs

try:
    from notion_client import Client
except ImportError:
    Client = None

logger = logging.getLogger(__name__)


class NotionSearcher:
    """Busca inteligente de páginas no Notion."""

    def __init__(self, api_key: str, database_id: str):
        if Client is None:
            raise ImportError("notion-client não instalado")

        self.client = Client(auth=api_key)
        self.database_id = database_id

    # -----------------------------
    # Helpers
    # -----------------------------

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower().replace("www.", "")
        path = parsed.path.rstrip("/")
        return f"{netloc}{path}"

    # -----------------------------
    # Searches
    # -----------------------------

    def search_by_url(self, mod_url: str) -> Optional[str]:
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
            logger.error(f"Erro na busca por URL {mod_url}: {e}")
            return None

    def fuzzy_search(self, query: str, limit: int = 5) -> List[Dict]:
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
                props = page["properties"]

                def text(prop, kind):
                    return (
                        prop.get(kind, [{}])[0].get("plain_text", "")
                        if prop and prop.get(kind)
                        else ""
                    )

                results.append({
                    "page_id": page["id"],
                    "name": text(props.get("Nome"), "title"),
                    "creator": text(props.get("Criador"), "rich_text"),
                    "url": props.get("Link", {}).get("url", ""),
                    "folder": props.get("Pasta", {}).get("select", {}).get("name", ""),
                    "priority": props.get("Prioridade", {}).get("select", {}).get("name", "")
                })

            return results

        except Exception as e:
            logger.error(f"Erro na busca fuzzy por '{query}': {e}")
            return []

    def search(self, query: str) -> List[Dict]:
        if query.startswith("http"):
            page_id = self.search_by_url(query)
            if not page_id:
                return []

            page = self.client.pages.retrieve(page_id)
            props = page["properties"]

            return [{
                "page_id": page_id,
                "name": props["Nome"]["title"][0]["plain_text"] if props["Nome"]["title"] else "",
                "creator": props["Criador"]["rich_text"][0]["plain_text"] if props["Criador"]["rich_text"] else "",
                "url": props["Link"]["url"],
                "folder": props["Pasta"]["select"]["name"] if props["Pasta"]["select"] else "",
                "priority": props["Prioridade"]["select"]["name"] if props["Prioridade"]["select"] else "",
            }]

        return self.fuzzy_search(query)
