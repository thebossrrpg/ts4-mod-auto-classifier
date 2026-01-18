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

    FOLDER_MAP = {
        1: "00 - Must Have",
        2: "01 - Core Gameplay",
        3: "02 - Quality of Life",
        4: "03 - Enhancements",
        5: "04 - Optional/Aesthetic"
    }

    def __init__(self, api_key: str, database_id: str):
        if Client is None:
            raise ImportError("notion-client não instalado. Instale com: pip install notion-client")

        self.client = Client(auth=api_key)
        self.database_id = database_id
        self._schema = None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def get_database_schema(self) -> Dict:
        """Obtém schema da database."""
        if self._schema is None:
            self._schema = self.client.databases.retrieve(self.database_id)
        return self._schema

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def get_page(self, page_id: str) -> Dict:
        """Obtém página do Notion."""
        return self.client.pages.retrieve(page_id)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def create_page(self, properties: Dict) -> str:
        """Cria nova página no Notion."""
        notion_properties = self._build_properties(properties)

        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=notion_properties
        )

        page_id = response["id"]
        logger.info(f"Página criada no Notion: {page_id}")
        return page_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def update_page(self, page_id: str, properties: Dict):
        """Atualiza página existente."""
        notion_properties = self._build_properties(properties)

        self.client.pages.update(
            page_id=page_id,
            properties=notion_properties
        )

        logger.info(f"Página atualizada no Notion: {page_id}")

    def _build_properties(self, props: Dict) -> Dict:
        """Converte propriedades simples para formato da API do Notion."""
        notion_props = {}

        def has_value(value):
            return value is not None and value != ""

        # Nome (Title)
        if has_value(props.get("name")):
            notion_props["Nome"] = {
                "title": [{"text": {"content": props["name"]}}]
            }

        # Criador (Rich Text)
        if has_value(props.get("creator")):
            notion_props["Criador"] = {
                "rich_text": [{"text": {"content": props["creator"]}}]
            }

        # Link (URL)
        if has_value(props.get("url")):
            notion_props["Link"] = {
                "url": props["url"]
            }

        # Prioridade (Select)
        if has_value(props.get("priority")):
            notion_props["Prioridade"] = {
                "select": {"name": str(props["priority"])}
            }

        # Pasta (Select)
        if has_value(props.get("folder")):
            folder = props["folder"]
            if isinstance(folder, int):
                folder = self.FOLDER_MAP.get(folder, "04 - Optional/Aesthetic")

            notion_props["Pasta"] = {
                "select": {"name": folder}
            }

        # Notes (Rich Text)
        if has_value(props.get("notes")):
            notion_props["Notes"] = {
                "rich_text": [{"text": {"content": props["notes"]}}]
            }

        return notion_props
