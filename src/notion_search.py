"""Cliente Notion completo para operações CRUD."""

import logging
from typing import Dict
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from notion_client import Client
except ImportError:
    Client = None

logger = logging.getLogger(__name__)


class NotionClient:
    """Cliente Notion com operações completas."""

    def __init__(self, api_key: str, database_id: str):
        """
        Inicializa cliente Notion.

        Args:
            api_key: Notion API key
            database_id: ID da database
        """
        if Client is None:
            raise ImportError("notion-client não instalado")

        self.client = Client(auth=api_key)
        self.database_id = database_id
        self._schema = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_database_schema(self) -> Dict:
        """Obtém schema da database."""
        if self._schema is None:
            self._schema = self.client.databases.retrieve(self.database_id)
        return self._schema

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_page(self, page_id: str) -> Dict:
        """Obtém página do Notion."""
        try:
            return self.client.pages.retrieve(page_id)
        except Exception as e:
            logger.error(f"Erro ao obter página {page_id}: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_page(self, properties: Dict) -> str:
        """
        Cria nova página no Notion.

        Args:
            properties: Propriedades da página

        Returns:
            Page ID da página criada
        """
        try:
            notion_properties = self._build_properties(properties)

            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=notion_properties
            )

            page_id = response["id"]
            logger.info(f"Página criada: {page_id}")
            return page_id

        except Exception as e:
            logger.error(f"Erro ao criar página: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def update_page(self, page_id: str, properties: Dict):
        """
        Atualiza página existente.

        Args:
            page_id: ID da página
            properties: Propriedades a atualizar
        """
        try:
            notion_properties = self._build_properties(properties)

            self.client.pages.update(
                page_id=page_id,
                properties=notion_properties
            )

            logger.info(f"Página atualizada: {page_id}")

        except Exception as e:
            logger.error(f"Erro ao atualizar página: {e}")
            raise

    def _build_properties(self, props: Dict) -> Dict:
        """
        Constrói propriedades no formato Notion.

        Args:
            props: Dicionário simples com as propriedades

        Returns:
            Propriedades no formato Notion API
        """
        notion_props = {}

        # Nome (Title)
        if props.get("name"):
            notion_props["Nome"] = {
                "title": [{"text": {"content": props["name"]}}]
            }

        # Criador (Rich Text)
        if props.get("creator"):
            notion_props["Criador"] = {
                "rich_text": [{"text": {"content": props["creator"]}}]
            }

        # Link (URL)
        if props.get("url"):
            notion_props["Link"] = {
                "url": props["url"]
            }

        # Prioridade (Select com opções numéricas)
        if "priority" in props and props["priority"] is not None:
            notion_props["Prioridade"] = {
                "select": {
                    "name": str(props["priority"])
                }
            }

        # Pasta (Select)
        if props.get("folder"):
            notion_props["Pasta"] = {
                "select": {
                    "name": props["folder"]
                }
            }

        # Notes (Rich Text)
        if props.get("notes"):
            notion_props["Notes"] = {
                "rich_text": [{"text": {"content": props["notes"]}}]
            }

        return notion_props
