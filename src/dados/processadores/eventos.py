"""
Módulo de processamento para detecção de eventos econômicos significativos.

Este módulo implementa classes e funções para identificar eventos
significativos em séries temporais de indicadores econômicos.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any, Tuple
import logging
from datetime import datetime, timedelta

# Configuração de logging
logger = logging.getLogger(__name__)

class DetectorEventos:
    """Classe para detecção de eventos significativos em séries temporais."""
    
    def __init__(self, sensibilidade: float = 1.5):
        """
        Inicializa o detector de eventos.
        
        Args:
            sensibilidade: Fator de sensibilidade para detecção de eventos (padrão: 1.5)
                           Valores maiores exigem mudanças mais significativas para detecção
        """
        self.sensibilidade = sensibilidade
        logger.info(f"DetectorEventos inicializado com sensibilidade: {self.sensibilidade}")
    
    def detectar_eventos(self, df: pd.DataFrame, 
                        coluna_data: str = 'data', 
                        coluna_valor: str = 'valor') -> pd.DataFrame:
        """
        Detecta eventos significativos em uma série temporal.
        
        Args:
            df: DataFrame com os dados da série temporal
            coluna_data: Nome da coluna de data
            coluna_valor: Nome da coluna de valor
            
        Returns:
            DataFrame com os eventos detectados (data, valor, tipo, descricao)
        """
        if df.empty or coluna_data not in df.columns or coluna_valor not in df.columns:
            logger.warning("DataFrame vazio ou colunas não encontradas")
            return pd.DataFrame(columns=['data', 'valor', 'tipo', 'descricao'])
        
        # Criar cópia para não modificar o original
        df_copia = df.copy()
        
        # Garantir que os dados estão ordenados por data
        df_copia = df_copia.sort_values(coluna_data)
        
        # Calcular variação percentual
        df_copia['variacao_pct'] = df_copia[coluna_valor].pct_change() * 100
        
        # Calcular média móvel e desvio padrão
        df_copia['media_movel'] = df_copia[coluna_valor].rolling(window=5, min_periods=1).mean()
        df_copia['desvio_padrao'] = df_copia[coluna_valor].rolling(window=12, min_periods=3).std()
        
        # Detectar eventos
        eventos = []
        
        # 1. Detectar picos e vales
        eventos.extend(self._detectar_picos_vales(df_copia, coluna_data, coluna_valor))
        
        # 2. Detectar mudanças abruptas
        eventos.extend(self._detectar_mudancas_abruptas(df_copia, coluna_data, coluna_valor))
        
        # 3. Detectar tendências
        eventos.extend(self._detectar_tendencias(df_copia, coluna_data, coluna_valor))
        
        # Criar DataFrame de eventos
        if eventos:
            df_eventos = pd.DataFrame(eventos)
            # Ordenar por data
            df_eventos = df_eventos.sort_values('data')
            # Remover eventos duplicados ou muito próximos
            df_eventos = self._filtrar_eventos_proximos(df_eventos)
            return df_eventos
        else:
            return pd.DataFrame(columns=['data', 'valor', 'tipo', 'descricao'])
    
    def _detectar_picos_vales(self, df: pd.DataFrame, 
                             coluna_data: str, 
                             coluna_valor: str) -> List[Dict[str, Any]]:
        """
        Detecta picos e vales na série temporal.
        
        Args:
            df: DataFrame com os dados
            coluna_data: Nome da coluna de data
            coluna_valor: Nome da coluna de valor
            
        Returns:
            Lista de eventos detectados
        """
        eventos = []
        
        # Precisamos de pelo menos 3 pontos para detectar picos/vales
        if len(df) < 3:
            return eventos
        
        # Calcular limiar baseado no desvio padrão
        limiar = df['desvio_padrao'].mean() * self.sensibilidade
        
        for i in range(1, len(df) - 1):
            valor_atual = df.iloc[i][coluna_valor]
            valor_anterior = df.iloc[i-1][coluna_valor]
            valor_posterior = df.iloc[i+1][coluna_valor]
            
            # Detectar pico
            if valor_atual > valor_anterior and valor_atual > valor_posterior:
                # Verificar se é significativo
                if (valor_atual - max(valor_anterior, valor_posterior)) > limiar:
                    eventos.append({
                        'data': df.iloc[i][coluna_data],
                        'valor': valor_atual,
                        'tipo': 'pico',
                        'descricao': f'Pico de {valor_atual:.2f}'
                    })
            
            # Detectar vale
            if valor_atual < valor_anterior and valor_atual < valor_posterior:
                # Verificar se é significativo
                if (min(valor_anterior, valor_posterior) - valor_atual) > limiar:
                    eventos.append({
                        'data': df.iloc[i][coluna_data],
                        'valor': valor_atual,
                        'tipo': 'vale',
                        'descricao': f'Vale de {valor_atual:.2f}'
                    })
        
        return eventos
    
    def _detectar_mudancas_abruptas(self, df: pd.DataFrame, 
                                   coluna_data: str, 
                                   coluna_valor: str) -> List[Dict[str, Any]]:
        """
        Detecta mudanças abruptas na série temporal.
        
        Args:
            df: DataFrame com os dados
            coluna_data: Nome da coluna de data
            coluna_valor: Nome da coluna de valor
            
        Returns:
            Lista de eventos detectados
        """
        eventos = []
        
        # Precisamos de pelo menos 2 pontos para detectar mudanças
        if len(df) < 2 or 'variacao_pct' not in df.columns:
            return eventos
        
        # Calcular limiar baseado na média das variações
        variacao_media = df['variacao_pct'].abs().mean()
        limiar = variacao_media * self.sensibilidade * 2
        
        for i in range(1, len(df)):
            variacao = df.iloc[i]['variacao_pct']
            
            # Ignorar valores NaN
            if pd.isna(variacao):
                continue
            
            # Detectar aumento abrupto
            if variacao > limiar:
                eventos.append({
                    'data': df.iloc[i][coluna_data],
                    'valor': df.iloc[i][coluna_valor],
                    'tipo': 'aumento_abrupto',
                    'descricao': f'Aumento abrupto de {variacao:.2f}%'
                })
            
            # Detectar queda abrupta
            elif variacao < -limiar:
                eventos.append({
                    'data': df.iloc[i][coluna_data],
                    'valor': df.iloc[i][coluna_valor],
                    'tipo': 'queda_abrupta',
                    'descricao': f'Queda abrupta de {abs(variacao):.2f}%'
                })
        
        return eventos
    
    def _detectar_tendencias(self, df: pd.DataFrame, 
                            coluna_data: str, 
                            coluna_valor: str) -> List[Dict[str, Any]]:
        """
        Detecta tendências na série temporal.
        
        Args:
            df: DataFrame com os dados
            coluna_data: Nome da coluna de data
            coluna_valor: Nome da coluna de valor
            
        Returns:
            Lista de eventos detectados
        """
        eventos = []
        
        # Precisamos de pelo menos 6 pontos para detectar tendências
        if len(df) < 6:
            return eventos
        
        # Calcular tendência usando média móvel
        janela = min(6, len(df) // 3)
        df['tendencia'] = df[coluna_valor].rolling(window=janela, min_periods=janela).mean()
        
        # Precisamos de pelo menos janela+1 pontos após calcular a tendência
        if df['tendencia'].isna().sum() > len(df) - janela - 1:
            return eventos
        
        # Detectar inversões de tendência
        tendencia_anterior = None
        for i in range(janela, len(df)):
            if i < janela + 2:
                continue
                
            # Calcular direção da tendência atual
            tendencia_atual = df.iloc[i]['tendencia'] - df.iloc[i-janela]['tendencia']
            
            # Pular se não temos tendência anterior
            if tendencia_anterior is None:
                tendencia_anterior = tendencia_atual
                continue
            
            # Detectar inversão de tendência
            if (tendencia_anterior > 0 and tendencia_atual < 0) or (tendencia_anterior < 0 and tendencia_atual > 0):
                # Verificar se é significativa
                if abs(tendencia_atual - tendencia_anterior) > df['desvio_padrao'].mean() * self.sensibilidade:
                    tipo = 'inversao_alta_baixa' if tendencia_anterior > 0 else 'inversao_baixa_alta'
                    descricao = 'Inversão de tendência de alta para baixa' if tendencia_anterior > 0 else 'Inversão de tendência de baixa para alta'
                    
                    eventos.append({
                        'data': df.iloc[i][coluna_data],
                        'valor': df.iloc[i][coluna_valor],
                        'tipo': tipo,
                        'descricao': descricao
                    })
            
            tendencia_anterior = tendencia_atual
        
        return eventos
    
    def _filtrar_eventos_proximos(self, df_eventos: pd.DataFrame, 
                                 dias_minimos: int = 30) -> pd.DataFrame:
        """
        Filtra eventos muito próximos, mantendo apenas os mais significativos.
        
        Args:
            df_eventos: DataFrame com os eventos
            dias_minimos: Número mínimo de dias entre eventos
            
        Returns:
            DataFrame filtrado
        """
        if df_eventos.empty or len(df_eventos) <= 1:
            return df_eventos
        
        # Ordenar por data
        df_eventos = df_eventos.sort_values('data')
        
        # Inicializar lista de eventos a manter
        eventos_filtrados = [df_eventos.iloc[0]]
        
        # Filtrar eventos próximos
        for i in range(1, len(df_eventos)):
            evento_atual = df_eventos.iloc[i]
            ultimo_evento = eventos_filtrados[-1]
            
            # Calcular diferença de dias
            dias_diff = (evento_atual['data'] - ultimo_evento['data']).days
            
            # Se estiver longe o suficiente, adicionar
            if dias_diff >= dias_minimos:
                eventos_filtrados.append(evento_atual)
            # Se for do mesmo tipo, manter apenas o mais significativo
            elif evento_atual['tipo'] == ultimo_evento['tipo']:
                # Para picos e vales, manter o mais extremo
                if evento_atual['tipo'] in ['pico', 'vale']:
                    if (evento_atual['tipo'] == 'pico' and evento_atual['valor'] > ultimo_evento['valor']) or \
                       (evento_atual['tipo'] == 'vale' and evento_atual['valor'] < ultimo_evento['valor']):
                        eventos_filtrados[-1] = evento_atual
                # Para outros tipos, manter o mais recente
                else:
                    eventos_filtrados[-1] = evento_atual
            # Se for de tipo diferente e for mais significativo, substituir
            elif evento_atual['tipo'] in ['aumento_abrupto', 'queda_abrupta'] and \
                 ultimo_evento['tipo'] not in ['aumento_abrupto', 'queda_abrupta']:
                eventos_filtrados[-1] = evento_atual
        
        return pd.DataFrame(eventos_filtrados)


# Função para execução direta do módulo
def main():
    """Função principal para execução direta do módulo."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Criar dados de exemplo
    datas = pd.date_range(start='2020-01-01', periods=100, freq='M')
    valores = np.random.normal(100, 10, 100)
    
    # Adicionar alguns eventos
    valores[20] = 150  # Pico
    valores[40] = 70   # Vale
    valores[60:70] = np.linspace(100, 130, 10)  # Tendência de alta
    valores[70:80] = np.linspace(130, 90, 10)   # Tendência de baixa
    
    # Criar DataFrame
    df = pd.DataFrame({'data': datas, 'valor': valores})
    
    # Detectar eventos
    detector = DetectorEventos()
    eventos = detector.detectar_eventos(df)
    
    # Exibir eventos
    logger.info(f"Eventos detectados: {len(eventos)}")
    if not eventos.empty:
        for _, evento in eventos.iterrows():
            logger.info(f"{evento['data'].strftime('%Y-%m-%d')}: {evento['descricao']}")


# Executar se for o módulo principal
if __name__ == "__main__":
    main()
