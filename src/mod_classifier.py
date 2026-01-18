"""Classificador de mods baseado na régua oficial v3.0 + sub-classificação."""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ModClassifier:
    """
    Classifica mods segundo a régua v3.0
    e gera sub-classificação textual para Notes.
    """

    PRIORITY_FOLDER_MAP = {
        0: "00 - Cosmético",
        1: "01 - Core",
        2: "02 - Sistemas",
        3: "03 - Gameplay",
        4: "04 - Persistente",
        5: "05 - Volátil"
    }

    # Sub-classificações (letra + etiqueta)
    SUBCLASS_RULES = [
        ("inventory", "5B", "Utilitários de Inventário e Gestão"),
        ("ui", "4A", "Ajustes de Interface"),
        ("framework", "1A", "Framework / Dependência"),
        ("career", "2B", "Sistemas de Carreira"),
        ("trait", "3A", "Traços e Personalidade"),
        ("aspiration", "3B", "Aspirações e Objetivos"),
        ("cas", "0A", "Itens CAS"),
    ]

    CORE_KEYWORDS = ["framework", "core", "library", "dependency"]
    SYSTEM_KEYWORDS = ["career", "pregnancy", "relationship", "calendar"]
    GAMEPLAY_KEYWORDS = ["interaction", "trait", "skill", "aspiration"]
    COSMETIC_KEYWORDS = ["cas", "hair", "clothing", "makeup"]

    def classify_mod(
        self,
        mod_name: str,
        mod_description: str = "",
        creator: str = ""
    ) -> Dict[str, object]:

        try:
            text = f"{mod_name} {mod_description} {creator}".lower()

            removal = self._estimate_removal_impact(text)
            framework = self._detect_framework(text)
            essential = self._estimate_essentiality(text)

            score = removal + framework + essential
            priority = self._score_to_priority(score)
            folder = self.PRIORITY_FOLDER_MAP[priority]

            subclass_note = self._detect_subclass(text)

            confidence = min(score / 8, 1.0)

            return {
                "priority": priority,
                "folder": folder,
                "confidence": round(confidence, 2),
                "score": score,
                "notes_suffix": subclass_note,
                "mod_name": mod_name
            }

        except Exception as e:
            logger.error(f"Erro ao classificar mod '{mod_name}': {e}")
            return {
                "priority": 4,
                "folder": self.PRIORITY_FOLDER_MAP[4],
                "confidence": 0.0,
                "score": 0,
                "notes_suffix": None,
                "mod_name": mod_name
            }

    # =====================
    # Heurísticas internas
    # =====================

    def _estimate_removal_impact(self, text: str) -> int:
        if any(k in text for k in self.CORE_KEYWORDS):
            return 4
        if any(k in text for k in self.SYSTEM_KEYWORDS):
            return 3
        if any(k in text for k in self.GAMEPLAY_KEYWORDS):
            return 2
        if any(k in text for k in self.COSMETIC_KEYWORDS):
            return 0
        return 1

    def _detect_framework(self, text: str) -> int:
        return 1 if any(k in text for k in self.CORE_KEYWORDS) else 0

    def _estimate_essentiality(self, text: str) -> int:
        if any(k in text for k in self.CORE_KEYWORDS):
            return 3
        if any(k in text for k in self.SYSTEM_KEYWORDS):
            return 2
        if any(k in text for k in self.GAMEPLAY_KEYWORDS):
            return 1
        return 0

    def _score_to_priority(self, score: int) -> int:
        if score >= 7:
            return 1
        if score >= 5:
            return 2
        if score >= 3:
            return 3
        if score == 2:
            return 4
        return 0

    def _detect_subclass(self, text: str) -> str | None:
        """
        Retorna string pronta para Notes:
        '5B — Utilitários de Inventário e Gestão'
        """
        for keyword, code, label in self.SUBCLASS_RULES:
            if keyword in text:
                return f"{code} — {label}"
        return None
