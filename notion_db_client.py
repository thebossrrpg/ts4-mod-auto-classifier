"""
Cliente Notion para operações CRUD + Notes.
"""

import logging
from typing import Dict

try:
    from notion_client import Client
except ImportError:
    Client = None

logger = logging.getLogger(__name__)


class NotionClient:
    def __init__(self, api_key: str, database_id: str):
        if Client is None:
            raise ImportError("notion-client não instalado")

        self.client = Client(auth=api_key)
        self.database_id = database_id

    # -----------------------------
    # CRUD
    # -----------------------------

    def get_page(self, page_id: str) -> Dict:
        return self.client.pages.retrieve(page_id)

    def create_page(self, properties: Dict) -> str:
        response = self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=self._build_properties(properties)
        )
        return response["id"]

    def update_page(self, page_id: str, properties: Dict):
        self.client.pages.update(
            page_id=page_id,
            properties=self._build_properties(properties)
        )

    # -----------------------------
    # Notes helpers
    # -----------------------------

    def append_to_notes(self, page_id: str, extra_line: str):
        page = self.get_page(page_id)
        props = page["properties"]

        existing = ""
        if props.get("Notes") and props["Notes"]["rich_text"]:
            existing = props["Notes"]["rich_text"][0]["plain_text"]

        new_notes = f"{existing}\n{extra_line}".strip()

        self.client.pages.update(
            page_id=page_id,
            properties={
                "Notes": {
                    "rich_text": [{"text": {"content": new_notes}}]
                }
            }
        )

    # -----------------------------
    # Property builder
    # -----------------------------

    def _build_properties(self, props: Dict) -> Dict:
        notion_props = {}

        if props.get("name"):
            notion_props["Nome"] = {
                "title": [{"text": {"content": props["name"]}}]
            }

        if props.get("creator"):
            notion_props["Criador"] = {
                "rich_text": [{"text": {"content": props["creator"]}}]
            }

        if props.get("url"):
            notion_props["Link"] = {"url": props["url"]}

        if props.get("priority") is not None:
            notion_props["Prioridade"] = {
                "select": {"name": str(props["priority"])}
            }

        if props.get("folder"):
            notion_props["Pasta"] = {
                "select": {"name": props["folder"]}
            }

        if props.get("notes"):
            notion_props["Notes"] = {
                "rich_text": [{"text": {"content": props["notes"]}}]
            }

        return notion_props
