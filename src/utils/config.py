"""
Sistema de Configuração Simplificado

Este módulo gerencia as configurações do dashboard de forma simples e eficiente.
"""

import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class ConfiguradorSimples:
    """Gerenciador de configurações simplificado"""
    
    def __init__(self):
        """Inicializa o configurador com valores padrão"""
        self._config = self._carregar_config_padrao()
    
    def _carregar_config_padrao(self) -> Dict[str, Any]:
        """Carrega configurações padrão"""
        return {
            'dashboard': {
                'titulo': 'Termômetro da Economia Brasileira',
                'subtitulo': 'Dashboard Interativo de Indicadores Econômicos',
                'desenvolvedor': 'Márcio Lemos',
                'versao': '2.0'
            },
            'cache': {
                'ttl_padrao': 3600,  # 1 hora
                'ttl_dados': 1800,   # 30 minutos
                'ttl_previsoes': 7200  # 2 horas
            },
            'indicadores': {
                'ipca': {
                    'nome': 'IPCA',
                    'unidade': '%',
                    'cor': '#FF6B6B',
                    'descricao': 'Índice de Preços ao Consumidor Amplo'
                },
                'selic': {
                    'nome': 'Taxa Selic',
                    'unidade': '% a.a.',
                    'cor': '#4ECDC4',
                    'descricao': 'Taxa básica de juros da economia'
                },
                'cambio': {
                    'nome': 'Câmbio USD/BRL',
                    'unidade': 'R$',
                    'cor': '#45B7D1',
                    'descricao': 'Taxa de câmbio Dólar/Real'
                },
                'deficit_primario': {
                    'nome': 'Déficit Primário',
                    'unidade': 'R$ bi',
                    'cor': '#96CEB4',
                    'descricao': 'Resultado primário do governo'
                },
                'iof': {
                    'nome': 'Arrecadação IOF',
                    'unidade': 'R$ mi',
                    'cor': '#FFEAA7',
                    'descricao': 'Imposto sobre Operações Financeiras'
                },
                'pib': {
                    'nome': 'PIB (Amostra)',
                    'unidade': '%',
                    'cor': '#DDA0DD',
                    'descricao': 'Produto Interno Bruto - variação trimestral'
                },
                'desemprego': {
                    'nome': 'Taxa de Desemprego (Amostra)',
                    'unidade': '%',
                    'cor': '#F8B500',
                    'descricao': 'Taxa de desocupação'
                }
            },
            'interface': {
                'layout': 'wide',
                'sidebar_inicial': 'expanded',
                'tema': 'light'
            }
        }
    
    def get(self, chave: str, padrao: Any = None) -> Any:
        """
        Obtém um valor de configuração
        
        Args:
            chave: Chave da configuração (ex: 'dashboard.titulo')
            padrao: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração ou padrão
        """
        try:
            # Navegar pela estrutura usando pontos
            valor = self._config
            for parte in chave.split('.'):
                valor = valor[parte]
            return valor
        except (KeyError, TypeError):
            return padrao
    
    def set(self, chave: str, valor: Any) -> None:
        """
        Define um valor de configuração
        
        Args:
            chave: Chave da configuração
            valor: Valor a ser definido
        """
        try:
            # Navegar e criar estrutura se necessário
            config_atual = self._config
            partes = chave.split('.')
            
            for parte in partes[:-1]:
                if parte not in config_atual:
                    config_atual[parte] = {}
                config_atual = config_atual[parte]
            
            config_atual[partes[-1]] = valor
        except Exception as e:
            logger.error(f"Erro ao definir configuração {chave}: {e}")
    
    def obter_config_indicador(self, indicador: str) -> Dict[str, Any]:
        """
        Obtém configuração completa de um indicador
        
        Args:
            indicador: ID do indicador
            
        Returns:
            Dicionário com configuração do indicador
        """
        return self.get(f'indicadores.{indicador}', {
            'nome': indicador.title(),
            'unidade': '',
            'cor': '#666666',
            'descricao': f'Indicador {indicador}'
        })
    
    def listar_indicadores(self) -> Dict[str, str]:
        """
        Lista todos os indicadores disponíveis
        
        Returns:
            Dicionário {id: nome} dos indicadores
        """
        indicadores = self.get('indicadores', {})
        return {
            id_ind: config.get('nome', id_ind.title())
            for id_ind, config in indicadores.items()
        }

# Instância global do configurador
config_manager = ConfiguradorSimples()

