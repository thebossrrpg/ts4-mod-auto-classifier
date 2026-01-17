"""Classificador de mods com análise de prioridade."""

import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


class ModClassifier:
    """Classifica mods baseado em palavras-chave e regras."""
    
    # Mapeamento de palavras-chave para prioridades
    KEYWORD_PRIORITIES = {
        # Prioridade 0 - Must Have
        "mccc": 0,
        "mc command center": 0,
        "ui cheats": 0,
        "better exceptions": 0,
        "basemental": 0,
        
        # Prioridade 1 - Core Gameplay
        "gameplay": 1,
        "career": 1,
        "traits": 1,
        "aspiration": 1,
        "buff": 1,
        "interaction": 1,
        
        # Prioridade 2 - Quality of Life
        "autonomy": 2,
        "faster": 2,
        "improved": 2,
        "better": 2,
        "enhancement": 2,
        
        # Prioridade 3 - Enhancements
        "cas": 3,
        "build": 3,
        "buy": 3,
        "animation": 3,
        "pose": 3,
        
        # Prioridade 4 - Optional/Aesthetic
        "clothing": 4,
        "hair": 4,
        "skin": 4,
        "makeup": 4,
        "accessory": 4,
        "decoration": 4,
    }
    
    # Mapeamento de prioridades para pastas
    PRIORITY_FOLDER_MAP = {
        0: "00 - Must Have",
        1: "01 - Core Gameplay",
        2: "02 - Quality of Life",
        3: "03 - Enhancements",
        4: "04 - Optional/Aesthetic"
    }
    
    def classify_mod(self, mod_name: str, mod_description: str = "", 
                     creator: str = "") -> Dict[str, any]:
        """
        Classifica um mod baseado em seu nome e descrição.
        
        Args:
            mod_name: Nome do mod
            mod_description: Descrição do mod
            creator: Nome do criador
            
        Returns:
            Dicionário com prioridade, pasta e confiança
        """
        try:
            # Combina texto para análise
            full_text = f"{mod_name} {mod_description} {creator}".lower()
            
            # Detecta prioridade baseado em palavras-chave
            detected_priority = self._detect_priority(full_text)
            
            # Mapeia para pasta
            folder = self.PRIORITY_FOLDER_MAP.get(detected_priority, 
                                                   "04 - Optional/Aesthetic")
            
            # Calcula confiança
            confidence = self._calculate_confidence(full_text, detected_priority)
            
            result = {
                "priority": detected_priority,
                "folder": folder,
                "confidence": confidence,
                "mod_name": mod_name
            }
            
            logger.info(f"Mod classificado: {mod_name} -> {folder} (confiança: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao classificar mod {mod_name}: {e}")
            # Retorna classificação padrão em caso de erro
            return {
                "priority": 4,
                "folder": "04 - Optional/Aesthetic",
                "confidence": 0.0,
                "mod_name": mod_name
            }
    
    def _detect_priority(self, text: str) -> int:
        """Detecta prioridade baseado em palavras-chave."""
        # Busca por palavras-chave
        matches = []
        for keyword, priority in self.KEYWORD_PRIORITIES.items():
            if keyword in text:
                matches.append(priority)
        
        # Retorna a menor prioridade encontrada (mais alta prioridade)
        if matches:
            return min(matches)
        
        # Padrão: Optional/Aesthetic
        return 4
    
    def _calculate_confidence(self, text: str, priority: int) -> float:
        """Calcula confiança da classificação."""
        # Conta quantas palavras-chave da prioridade foram encontradas
        relevant_keywords = [k for k, p in self.KEYWORD_PRIORITIES.items() 
                            if p == priority]
        
        matches = sum(1 for keyword in relevant_keywords if keyword in text)
        
        if not relevant_keywords:
            return 0.5  # Confiança média para classificação padrão
        
        # Confiança baseada em porcentagem de matches
        confidence = min(matches / len(relevant_keywords) * 2, 1.0)
        return confidence
    
    def classify_batch(self, mods: List[Dict]) -> List[Dict]:
        """
        Classifica múltiplos mods.
        
        Args:
            mods: Lista de dicionários com info dos mods
            
        Returns:
            Lista de classificações
        """
        results = []
        for mod in mods:
            name = mod.get("name", "")
            description = mod.get("description", "")
            creator = mod.get("creator", "")
            
            classification = self.classify_mod(name, description, creator)
            results.append(classification)
        
        logger.info(f"Classificados {len(results)} mods em lote")
        return results
