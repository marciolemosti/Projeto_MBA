"""
Módulo de utilitários para o Dashboard Econômico

Este módulo contém utilitários essenciais para o funcionamento do dashboard.
"""

from .cache import cache_manager, dataframe_cache
from .config import config_manager

__all__ = [
    'cache_manager',
    'dataframe_cache', 
    'config_manager'
]

