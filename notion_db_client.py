"""
Cliente Notion completo para operações CRUD.
Responsável por escrita e atualização.
"""

import logging
from typing import Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from notion_client import Client

logger = logging.getLogger(__name__)


class NotionClient:
    """Cliente Notion com operações completas (CRUD)."""

    def __init__(self, api_key: str, database_id: str):
        self.client = Client(auth=api_key)
        self.database_id = database_id

    # --------------------------------------------------
    # CRUD
    # --------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def get_page(self, page_id: str) -> Dict:
        return self.client.pages.retrieve(page_id)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def create_page(self, properties: Dict) -> str:
        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=self._build_properties(properties)
        )
        page_id = response["id"]
        logger.info(f"Página criada no Notion: {page_id}")
        return page_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def update_page(self, page_id: str, properties: Dict):
        self.client.pages.update(
            page_id=page_id,
            properties=self._build_properties(properties)
        )
        logger.info(f"Página atualizada no Notion: {page_id}")

    # --------------------------------------------------
    # Notes helpers
    # --------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    def append_to_notes(self, page_id: str, extra_line: str):
        """
        Acrescenta uma linha ao campo Notes sem sobrescrever conteúdo existente.
        Exemplo de uso:
        "5B — Utilitários de Inventário e Gestão"
        """
        page = self.get_page(page_id)
        props = page.get("properties", {})

        existing_lines = []

        notes_prop = props.get("Notes")
        if notes_prop and notes_prop.get("rich_text"):
            for block in notes_prop["rich_text"]:
                text = block.get("plain_text")
                if text:
                    existing_lines.append(text)

        # Evita duplicação
        if extra_line in existing_lines:
            logger.info("Linha já existe em Notes, ignorando append.")
            return

        existing_lines.append(extra_line)
        new_notes = "\n".join(existing_lines)

        self.client.pages.update(
            page_id=page_id,
            properties={
                "Notes": {
                    "rich_text": [
                        {"text": {"content": new_notes}}
                    ]
                }
            }
        )

        logger.info(f"Linha adicionada em Notes ({page_id})")

    # --------------------------------------------------
    # Property builder
    # --------------------------------------------------

    def _build_properties(self, props: Dict) -> Dict:
        """
        Constrói propriedades no formato esperado pela API do Notion.
        """
        notion_props = {}

        # Nome (Title)
        if props.get("name"):
            notion_props["Nome"] = {
                "title": [
                    {"text": {"content": props["name"]}}
                ]
            }

        # Criador (Rich Text)
        if props.get("creator"):
            notion_props["Criador"] = {
                "rich_text": [
                    {"text": {"content": props["creator"]}}
                ]
            }

        # Link (URL)
        if props.get("url"):
            notion_props["Link"] = {
                "url": props["url"]
            }

        # Prioridade (Select com opções numéricas)
        if props.get("priority") is not None:
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

        # Notes (Rich Text – sobrescreve apenas quando usado em create/update)
        if props.get("notes"):
            notion_props["Notes"] = {
                "rich_text": [
                    {"text": {"content": props["notes"]}}
                ]
            }

        return notion_props
