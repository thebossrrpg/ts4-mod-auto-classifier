"""Classificador de mods baseado na régua oficial v3.0 de prioridades."""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ModClassifier:
    """
    Classifica mods do The Sims 4 segundo a régua v3.0:
    Score = Remoção + Framework + Essencial
    """

    # =========================
    # Mapeamentos oficiais
    # =========================

    PRIORITY_FOLDER_MAP = {
        0: "00 - Cosmético",
        1: "01 - Core",
        2: "02 - Sistemas",
        3: "03 - Gameplay",
        4: "04 - Persistente",
        5: "05 - Volátil"
    }

    # Heurísticas básicas (ajustáveis depois)
    CORE_KEYWORDS = [
        "framework", "core", "injector", "library", "dependency"
    ]

    SYSTEM_KEYWORDS = [
        "career", "pregnancy", "relationship", "emotion", "calendar",
        "finance", "death", "school", "education", "overhaul"
    ]

    GAMEPLAY_KEYWORDS = [
        "event", "interaction", "buff", "trait", "skill",
        "aspiration", "holiday", "festival", "object"
    ]

    COSMETIC_KEYWORDS = [
        "override", "map", "loading screen", "font", "ui recolor"
    ]

    # =========================
    # API pública
    # =========================

    def classify_mod(
        self,
        mod_name: str,
        mod_description: str = "",
        creator: str = ""
    ) -> Dict[str, object]:
        """
        Classifica um mod e retorna dados prontos para o Notion.
        """
        try:
            text = f"{mod_name} {mod_description} {creator}".lower()

            removal = self._estimate_removal_impact(text)
            framework = self._detect_framework(text)
            essential = self._estimate_essentiality(text)

            score = removal + framework + essential
            priority = self._score_to_priority(score)
            folder = self.PRIORITY_FOLDER_MAP[priority]

            confidence = min(score / 8, 1.0)

            result = {
                "priority": priority,   # SELECT numérico
                "folder": folder,
                "confidence": round(confidence, 2),
                "score": score,
                "mod_name": mod_name
            }

            logger.info(
                f"Classificação: {mod_name} | "
                f"score={score} -> priority={priority}"
            )
            return result

        except Exception as e:
            logger.error(f"Erro ao classificar mod '{mod_name}': {e}")
            return {
                "priority": 4,
                "folder": self.PRIORITY_FOLDER_MAP[4],
                "confidence": 0.0,
                "score": 0,
                "mod_name": mod_name
            }

    def classify_batch(self, mods: List[Dict]) -> List[Dict]:
        """Classifica vários mods de uma vez."""
        results = []
        for mod in mods:
            results.append(
                self.classify_mod(
                    mod.get("name", ""),
                    mod.get("description", ""),
                    mod.get("creator", "")
                )
            )
        return results

    # =========================
    # Heurísticas internas
    # =========================

    def _estimate_removal_impact(self, text: str) -> int:
        """
        Impacto de remoção (0–4)
        """
        if any(k in text for k in self.CORE_KEYWORDS):
            return 4

        if any(k in text for k in self.SYSTEM_KEYWORDS):
            return 3

        if any(k in text for k in self.GAMEPLAY_KEYWORDS):
            return 2

        if any(k in text for k in self.COSMETIC_KEYWORDS):
            return 0

        return 1  # padrão conservador

    def _detect_framework(self, text: str) -> int:
        """Detecta se é framework/core."""
        return 1 if any(k in text for k in self.CORE_KEYWORDS) else 0

    def _estimate_essentiality(self, text: str) -> int:
        """
        Essencialidade genérica (0–3)
        """
        if any(k in text for k in self.CORE_KEYWORDS):
            return 3

        if any(k in text for k in self.SYSTEM_KEYWORDS):
            return 2

        if any(k in text for k in self.GAMEPLAY_KEYWORDS):
            return 1

        return 0

    def _score_to_priority(self, score: int) -> int:
        """
        Conversão oficial score → prioridade
        """
        if score >= 7:
            return 1  # Vermelho
        if score >= 5:
            return 2  # Amarelo
        if score >= 3:
            return 3  # Verde
        if score == 2:
            return 4  # Azul
        if score <= 1:
            return 0  # Cinza

        return 4
