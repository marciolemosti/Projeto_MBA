"""
Sistema de Cache Simplificado para o Dashboard Econômico

Este módulo implementa um sistema de cache leve e eficiente
para otimizar o carregamento de dados no dashboard.
"""

import os
import json
import time
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheSimples:
    """Sistema de cache simples em memória"""
    
    def __init__(self, ttl_padrao: int = 3600):
        """
        Inicializa o cache simples
        
        Args:
            ttl_padrao: Tempo de vida padrão em segundos (1 hora)
        """
        self._cache: Dict[str, Dict] = {}
        self.ttl_padrao = ttl_padrao
    
    def get(self, chave: str) -> Optional[Any]:
        """
        Recupera um item do cache
        
        Args:
            chave: Chave do item
            
        Returns:
            Valor armazenado ou None se não encontrado/expirado
        """
        if chave not in self._cache:
            return None
        
        item = self._cache[chave]
        
        # Verificar se expirou
        if time.time() > item['expira_em']:
            del self._cache[chave]
            return None
        
        return item['valor']
    
    def set(self, chave: str, valor: Any, ttl: Optional[int] = None) -> None:
        """
        Armazena um item no cache
        
        Args:
            chave: Chave do item
            valor: Valor a ser armazenado
            ttl: Tempo de vida em segundos (usa padrão se None)
        """
        if ttl is None:
            ttl = self.ttl_padrao
        
        self._cache[chave] = {
            'valor': valor,
            'criado_em': time.time(),
            'expira_em': time.time() + ttl
        }
    
    def clear(self) -> None:
        """Limpa todo o cache"""
        self._cache.clear()
        logger.info("Cache limpo")
    
    def limpar_expirados(self) -> int:
        """
        Remove itens expirados do cache
        
        Returns:
            Número de itens removidos
        """
        agora = time.time()
        chaves_expiradas = [
            chave for chave, item in self._cache.items()
            if agora > item['expira_em']
        ]
        
        for chave in chaves_expiradas:
            del self._cache[chave]
        
        return len(chaves_expiradas)
    
    def estatisticas(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do cache
        
        Returns:
            Dicionário com estatísticas
        """
        agora = time.time()
        itens_validos = sum(
            1 for item in self._cache.values()
            if agora <= item['expira_em']
        )
        
        return {
            'total_itens': len(self._cache),
            'itens_validos': itens_validos,
            'itens_expirados': len(self._cache) - itens_validos,
            'tamanho_mb': len(str(self._cache)) / (1024 * 1024)
        }

# Instância global do cache
cache_manager = CacheSimples()

# Cache específico para DataFrames (alias para compatibilidade)
dataframe_cache = cache_manager

