"""
Módulo de processamento para previsão de séries temporais.

Este módulo implementa classes e funções para processamento e previsão
de séries temporais de indicadores econômicos, incluindo PIB, desemprego,
déficit primário, IOF, entre outros.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple

# Importação opcional do Prophet
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    Prophet = None

# Configuração de logging
logger = logging.getLogger(__name__)

class PrevisorSeriesTemporal:
    """Classe para previsão de séries temporais usando Prophet."""
    
    def __init__(self, intervalo_confianca: float = 0.95, 
                horizonte_anos: int = 2, 
                sazonalidade_semanal: bool = False,
                sazonalidade_anual: bool = True):
        """
        Inicializa o previsor de séries temporais.
        
        Args:
            intervalo_confianca: Intervalo de confiança para previsões (0 a 1)
            horizonte_anos: Horizonte de previsão em anos
            sazonalidade_semanal: Se deve considerar sazonalidade semanal
            sazonalidade_anual: Se deve considerar sazonalidade anual
        """
        self.intervalo_confianca = intervalo_confianca
        self.horizonte_anos = horizonte_anos
        self.sazonalidade_semanal = sazonalidade_semanal
        self.sazonalidade_anual = sazonalidade_anual
        self.modelo = None
        self.dados_preparados = None
        self.periodicidade = None
        logger.info(f"PrevisorSeriesTemporal inicializado com horizonte de {horizonte_anos} anos")
    
    def preparar_dados(self, df: pd.DataFrame, 
                      coluna_data: str = 'data', 
                      coluna_valor: str = 'valor') -> pd.DataFrame:
        """
        Prepara os dados para previsão com Prophet.
        
        Args:
            df: DataFrame com os dados
            coluna_data: Nome da coluna de data
            coluna_valor: Nome da coluna de valor
            
        Returns:
            DataFrame preparado para Prophet (colunas 'ds' e 'y')
        """
        if df.empty or coluna_data not in df.columns or coluna_valor not in df.columns:
            logger.warning("DataFrame vazio ou colunas não encontradas")
            return pd.DataFrame(columns=['ds', 'y'])
        
        # Criar cópia para não modificar o original
        df_prophet = df.copy()
        
        # Renomear colunas para o formato do Prophet
        df_prophet = df_prophet.rename(columns={coluna_data: 'ds', coluna_valor: 'y'})
        
        # Selecionar apenas as colunas necessárias
        df_prophet = df_prophet[['ds', 'y']]
        
        # Remover valores nulos
        df_prophet = df_prophet.dropna()
        
        # Ordenar por data
        df_prophet = df_prophet.sort_values('ds')
        
        # Detectar periodicidade dos dados
        self._detectar_periodicidade(df_prophet)
        
        # Armazenar dados preparados
        self.dados_preparados = df_prophet
        
        logger.info(f"Dados preparados para previsão: {len(df_prophet)} registros, periodicidade {self.periodicidade}")
        return df_prophet
    
    def _detectar_periodicidade(self, df: pd.DataFrame) -> None:
        """
        Detecta a periodicidade dos dados.
        
        Args:
            df: DataFrame com os dados preparados
        """
        if len(df) < 2:
            self.periodicidade = 'desconhecida'
            return
        
        # Calcular diferenças entre datas consecutivas
        diffs = []
        for i in range(1, min(10, len(df))):
            diff_dias = (df.iloc[i]['ds'] - df.iloc[i-1]['ds']).days
            if diff_dias > 0:
                diffs.append(diff_dias)
        
        if not diffs:
            self.periodicidade = 'desconhecida'
            return
        
        # Calcular mediana das diferenças
        mediana_diff = np.median(diffs)
        
        # Determinar periodicidade
        if mediana_diff <= 1:
            self.periodicidade = 'diaria'
        elif mediana_diff <= 7:
            self.periodicidade = 'semanal'
        elif mediana_diff <= 15:
            self.periodicidade = 'quinzenal'
        elif mediana_diff <= 45:
            self.periodicidade = 'mensal'
        elif mediana_diff <= 100:
            self.periodicidade = 'trimestral'
        elif mediana_diff <= 200:
            self.periodicidade = 'semestral'
        else:
            self.periodicidade = 'anual'
    
    def treinar(self, df_prophet: Optional[pd.DataFrame] = None) -> bool:
        """
        Treina o modelo Prophet com os dados preparados.
        
        Args:
            df_prophet: DataFrame preparado para Prophet (opcional, usa dados_preparados se None)
            
        Returns:
            True se o treinamento foi bem-sucedido, False caso contrário
        """
        # Usar dados preparados anteriormente se não fornecidos
        if df_prophet is None:
            df_prophet = self.dados_preparados
        
        if df_prophet is None or df_prophet.empty:
            logger.warning("Sem dados para treinar o modelo")
            return False
        
        try:
            # Configurar modelo Prophet
            self.modelo = Prophet(
                interval_width=self.intervalo_confianca,
                weekly_seasonality=self.sazonalidade_semanal,
                yearly_seasonality=self.sazonalidade_anual
            )
            
            # Ajustar sazonalidades com base na periodicidade
            if self.periodicidade in ['diaria', 'semanal']:
                self.modelo.add_seasonality(name='weekly', period=7, fourier_order=3)
            
            if self.periodicidade in ['diaria', 'semanal', 'quinzenal', 'mensal']:
                self.modelo.add_seasonality(name='yearly', period=365.25, fourier_order=5)
            
            if self.periodicidade in ['trimestral', 'semestral']:
                self.modelo.add_seasonality(name='yearly', period=4, fourier_order=3)
            
            # Treinar modelo
            self.modelo.fit(df_prophet)
            
            logger.info("Modelo Prophet treinado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao treinar modelo Prophet: {str(e)}")
            self.modelo = None
            return False
    
    def prever(self, periodos: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Realiza previsão com o modelo treinado.
        
        Args:
            periodos: Número de períodos a prever (opcional, usa horizonte_anos se None)
            
        Returns:
            DataFrame com as previsões ou None se falhar
        """
        if self.modelo is None:
            logger.warning("Modelo não treinado. Use treinar() primeiro.")
            return None
        
        try:
            # Determinar número de períodos com base no horizonte e periodicidade
            if periodos is None:
                if self.periodicidade == 'diaria':
                    periodos = self.horizonte_anos * 365
                elif self.periodicidade == 'semanal':
                    periodos = self.horizonte_anos * 52
                elif self.periodicidade == 'quinzenal':
                    periodos = self.horizonte_anos * 26
                elif self.periodicidade == 'mensal':
                    periodos = self.horizonte_anos * 12
                elif self.periodicidade == 'trimestral':
                    periodos = self.horizonte_anos * 4
                elif self.periodicidade == 'semestral':
                    periodos = self.horizonte_anos * 2
                elif self.periodicidade == 'anual':
                    periodos = self.horizonte_anos
                else:
                    periodos = self.horizonte_anos * 12  # Padrão: mensal
            
            # Criar DataFrame futuro
            df_futuro = self.modelo.make_future_dataframe(
                periods=periodos,
                freq=self._obter_frequencia_pandas()
            )
            
            # Fazer previsão
            previsao = self.modelo.predict(df_futuro)
            
            logger.info(f"Previsão realizada para {periodos} períodos")
            return previsao
            
        except Exception as e:
            logger.error(f"Erro ao realizar previsão: {str(e)}")
            return None
    
    def _obter_frequencia_pandas(self) -> str:
        """
        Obtém a string de frequência do pandas com base na periodicidade detectada.
        
        Returns:
            String de frequência do pandas
        """
        if self.periodicidade == 'diaria':
            return 'D'
        elif self.periodicidade == 'semanal':
            return 'W'
        elif self.periodicidade == 'quinzenal':
            return '2W'
        elif self.periodicidade == 'mensal':
            return 'M'
        elif self.periodicidade == 'trimestral':
            return 'Q'
        elif self.periodicidade == 'semestral':
            return '6M'
        elif self.periodicidade == 'anual':
            return 'Y'
        else:
            return 'M'  # Padrão: mensal
    
    def obter_dados_previsao(self, previsao: Optional[pd.DataFrame] = None, 
                           incluir_historico: bool = True) -> pd.DataFrame:
        """
        Obtém os dados de previsão em formato simplificado.
        
        Args:
            previsao: DataFrame com as previsões (opcional, realiza nova previsão se None)
            incluir_historico: Se deve incluir dados históricos na saída
            
        Returns:
            DataFrame com colunas 'data', 'valor', 'limite_inferior', 'limite_superior', 'tipo'
        """
        if previsao is None:
            previsao = self.prever()
        
        if previsao is None or previsao.empty:
            logger.warning("Sem dados de previsão disponíveis")
            return pd.DataFrame(columns=['data', 'valor', 'limite_inferior', 'limite_superior', 'tipo'])
        
        # Criar DataFrame de saída
        df_saida = pd.DataFrame({
            'data': previsao['ds'],
            'valor': previsao['yhat'],
            'limite_inferior': previsao['yhat_lower'],
            'limite_superior': previsao['yhat_upper']
        })
        
        # Adicionar coluna de tipo (histórico ou previsão)
        if self.dados_preparados is not None and not self.dados_preparados.empty:
            ultima_data_historico = self.dados_preparados['ds'].max()
            df_saida['tipo'] = df_saida['data'].apply(
                lambda x: 'histórico' if x <= ultima_data_historico else 'previsão'
            )
            
            # Substituir valores previstos por valores históricos reais
            if incluir_historico:
                # Mesclar com dados históricos
                df_historico = self.dados_preparados.copy()
                df_historico = df_historico.rename(columns={'ds': 'data', 'y': 'valor_real'})
                
                # Mesclar por data
                df_saida = pd.merge(df_saida, df_historico[['data', 'valor_real']], 
                                   on='data', how='left')
                
                # Substituir valores previstos por valores reais onde disponíveis
                mask = ~df_saida['valor_real'].isna()
                df_saida.loc[mask, 'valor'] = df_saida.loc[mask, 'valor_real']
                
                # Remover coluna temporária
                df_saida = df_saida.drop(columns=['valor_real'])
            
            # Filtrar apenas previsões se não incluir histórico
            if not incluir_historico:
                df_saida = df_saida[df_saida['tipo'] == 'previsão']
        else:
            # Se não temos dados históricos, considerar tudo como previsão
            df_saida['tipo'] = 'previsão'
        
        # Ordenar por data
        df_saida = df_saida.sort_values('data')
        
        return df_saida
    
    def avaliar_modelo(self) -> Dict[str, float]:
        """
        Avalia o desempenho do modelo usando validação cruzada.
        
        Returns:
            Dicionário com métricas de avaliação
        """
        if self.modelo is None or self.dados_preparados is None or self.dados_preparados.empty:
            logger.warning("Modelo não treinado ou sem dados para avaliação")
            return {}
        
        try:
            from prophet.diagnostics import cross_validation, performance_metrics
            
            # Determinar parâmetros de validação cruzada com base na periodicidade
            if self.periodicidade == 'diaria':
                initial = '180 days'
                period = '90 days'
                horizon = '30 days'
            elif self.periodicidade == 'semanal':
                initial = '24 weeks'
                period = '12 weeks'
                horizon = '4 weeks'
            elif self.periodicidade == 'mensal':
                initial = '24 months'
                period = '6 months'
                horizon = '3 months'
            elif self.periodicidade in ['trimestral', 'semestral', 'anual']:
                initial = '3 years'
                period = '1 year'
                horizon = '1 year'
            else:
                initial = '365 days'
                period = '180 days'
                horizon = '90 days'
            
            # Realizar validação cruzada
            df_cv = cross_validation(
                model=self.modelo,
                initial=initial,
                period=period,
                horizon=horizon,
                parallel="processes"
            )
            
            # Calcular métricas
            df_p = performance_metrics(df_cv)
            
            # Extrair métricas principais
            metricas = {
                'mae': df_p['mae'].mean(),
                'rmse': df_p['rmse'].mean(),
                'mape': df_p['mape'].mean() if 'mape' in df_p.columns else None
            }
            
            logger.info(f"Avaliação do modelo: MAE={metricas['mae']:.4f}, RMSE={metricas['rmse']:.4f}")
            return metricas
            
        except Exception as e:
            logger.error(f"Erro ao avaliar modelo: {str(e)}")
            return {}


# Funções para processamento de indicadores específicos

def processar_dados_pib(dados_brutos: Union[pd.DataFrame, List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Processa dados brutos do PIB para formato padronizado.
    
    Args:
        dados_brutos: DataFrame ou lista de dicionários com dados do PIB
        
    Returns:
        DataFrame processado com colunas 'data' e 'valor'
    """
    logger.info("Processando dados do PIB")
    
    # Converter para DataFrame se for lista
    if isinstance(dados_brutos, list):
        df = pd.DataFrame(dados_brutos)
    else:
        df = dados_brutos.copy()
    
    # Verificar se DataFrame está vazio
    if df.empty:
        logger.warning("Dados do PIB vazios")
        return pd.DataFrame(columns=['data', 'valor'])
    
    # Garantir que temos as colunas necessárias
    colunas_necessarias = ['data', 'valor']
    if not all(col in df.columns for col in colunas_necessarias):
        logger.warning(f"Colunas necessárias não encontradas nos dados do PIB: {colunas_necessarias}")
        return pd.DataFrame(columns=['data', 'valor'])
    
    # Converter data para datetime se não for
    if not pd.api.types.is_datetime64_any_dtype(df['data']):
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
    
    # Converter valor para numérico
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    
    # Remover linhas com valores nulos
    df = df.dropna(subset=['data', 'valor'])
    
    # Selecionar apenas as colunas necessárias
    df = df[colunas_necessarias]
    
    # Ordenar por data
    df = df.sort_values('data')
    
    logger.info(f"Dados do PIB processados: {len(df)} registros")
    return df

def processar_dados_desemprego(dados_brutos: Union[pd.DataFrame, List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Processa dados brutos da taxa de desemprego para formato padronizado.
    
    Args:
        dados_brutos: DataFrame ou lista de dicionários com dados da taxa de desemprego
        
    Returns:
        DataFrame processado com colunas 'data' e 'valor'
    """
    logger.info("Processando dados da taxa de desemprego")
    
    # Converter para DataFrame se for lista
    if isinstance(dados_brutos, list):
        df = pd.DataFrame(dados_brutos)
    else:
        df = dados_brutos.copy()
    
    # Verificar se DataFrame está vazio
    if df.empty:
        logger.warning("Dados da taxa de desemprego vazios")
        return pd.DataFrame(columns=['data', 'valor'])
    
    # Garantir que temos as colunas necessárias
    colunas_necessarias = ['data', 'valor']
    if not all(col in df.columns for col in colunas_necessarias):
        logger.warning(f"Colunas necessárias não encontradas nos dados da taxa de desemprego: {colunas_necessarias}")
        return pd.DataFrame(columns=['data', 'valor'])
    
    # Converter data para datetime se não for
    if not pd.api.types.is_datetime64_any_dtype(df['data']):
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
    
    # Converter valor para numérico
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    
    # Remover linhas com valores nulos
    df = df.dropna(subset=['data', 'valor'])
    
    # Selecionar apenas as colunas necessárias
    df = df[colunas_necessarias]
    
    # Ordenar por data
    df = df.sort_values('data')
    
    logger.info(f"Dados da taxa de desemprego processados: {len(df)} registros")
    return df

def processar_dados_deficit(dados_brutos: Union[pd.DataFrame, List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Processa dados brutos do déficit primário para formato padronizado.
    
    Args:
        dados_brutos: DataFrame ou lista de dicionários com dados do déficit primário
        
    Returns:
        DataFrame processado com colunas 'data' e 'valor'
    """
    logger.info("Processando dados do déficit primário")
    
    # Converter para DataFrame se for lista
    if isinstance(dados_brutos, list):
        df = pd.DataFrame(dados_brutos)
    else:
        df = dados_brutos.copy()
    
    # Verificar se DataFrame está vazio
    if df.empty:
        logger.warning("Dados do déficit primário vazios")
        return pd.DataFrame(columns=['data', 'valor'])
    
    # Garantir que temos as colunas necessárias
    colunas_necessarias = ['data']
    if not all(col in df.columns for col in colunas_necessarias):
        logger.warning(f"Colunas necessárias não encontradas nos dados do déficit primário: {colunas_necessarias}")
        return pd.DataFrame(columns=['data', 'valor'])
    
    # Converter data para datetime se não for
    if not pd.api.types.is_datetime64_any_dtype(df['data']):
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
    
    # Identificar coluna de valor (pode ser 'valor', 'deficit', etc.)
    coluna_valor = None
    for col in ['valor', 'deficit', 'deficit_primario']:
        if col in df.columns:
            coluna_valor = col
            break
    
    # Se não encontrou coluna de valor, retornar vazio
    if coluna_valor is None:
        logger.warning("Coluna de valor não encontrada nos dados do déficit primário")
        return pd.DataFrame(columns=['data', 'valor'])
    
    # Criar cópia com colunas padronizadas
    df_processado = pd.DataFrame({
        'data': df['data'],
        'valor': pd.to_numeric(df[coluna_valor], errors='coerce')
    })
    
    # Remover linhas com valores nulos
    df_processado = df_processado.dropna()
    
    # Ordenar por data
    df_processado = df_processado.sort_values('data')
    
    logger.info(f"Dados do déficit primário processados: {len(df_processado)} registros")
    return df_processado

def processar_dados_iof(dados_brutos: Union[pd.DataFrame, List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Processa dados brutos da arrecadação de IOF para formato padronizado.
    
    Args:
        dados_brutos: DataFrame ou lista de dicionários com dados da arrecadação de IOF
        
    Returns:
        DataFrame processado com colunas 'data' e 'valor'
    """
    logger.info("Processando dados da arrecadação de IOF")
    
    # Converter para DataFrame se for lista
    if isinstance(dados_brutos, list):
        df = pd.DataFrame(dados_brutos)
    else:
        df = dados_brutos.copy()
    
    # Verificar se DataFrame está vazio
    if df.empty:
        logger.warning("Dados da arrecadação de IOF vazios")
        return pd.DataFrame(columns=['data', 'valor'])
    
    # Garantir que temos as colunas necessárias
    colunas_necessarias = ['data']
    if not all(col in df.columns for col in colunas_necessarias):
        logger.warning(f"Colunas necessárias não encontradas nos dados da arrecadação de IOF: {colunas_necessarias}")
        return pd.DataFrame(columns=['data', 'valor'])
    
    # Converter data para datetime se não for
    if not pd.api.types.is_datetime64_any_dtype(df['data']):
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
    
    # Identificar coluna de valor (pode ser 'valor', 'iof', etc.)
    coluna_valor = None
    for col in ['valor', 'iof', 'arrecadacao']:
        if col in df.columns:
            coluna_valor = col
            break
    
    # Se não encontrou coluna de valor, retornar vazio
    if coluna_valor is None:
        logger.warning("Coluna de valor não encontrada nos dados da arrecadação de IOF")
        return pd.DataFrame(columns=['data', 'valor'])
    
    # Criar cópia com colunas padronizadas
    df_processado = pd.DataFrame({
        'data': df['data'],
        'valor': pd.to_numeric(df[coluna_valor], errors='coerce')
    })
    
    # Remover linhas com valores nulos
    df_processado = df_processado.dropna()
    
    # Ordenar por data
    df_processado = df_processado.sort_values('data')
    
    logger.info(f"Dados da arrecadação de IOF processados: {len(df_processado)} registros")
    return df_processado

def gerar_previsoes_para_indicadores(dados_indicadores: Dict[str, pd.DataFrame], 
                                   horizonte_anos: int = 2) -> Dict[str, pd.DataFrame]:
    """
    Gera previsões para múltiplos indicadores.
    
    Args:
        dados_indicadores: Dicionário com DataFrames dos indicadores
        horizonte_anos: Horizonte de previsão em anos
        
    Returns:
        Dicionário com DataFrames das previsões
    """
    logger.info(f"Gerando previsões para {len(dados_indicadores)} indicadores com horizonte de {horizonte_anos} anos")
    
    previsoes = {}
    
    for nome_indicador, df in dados_indicadores.items():
        if df.empty:
            logger.warning(f"Dados vazios para {nome_indicador}, pulando previsão")
            continue
        
        try:
            # Criar previsor
            previsor = PrevisorSeriesTemporal(horizonte_anos=horizonte_anos)
            
            # Preparar dados
            df_preparado = previsor.preparar_dados(df)
            
            # Treinar modelo
            sucesso = previsor.treinar(df_preparado)
            
            if sucesso:
                # Gerar previsão
                previsao = previsor.prever()
                
                if previsao is not None:
                    # Obter dados de previsão em formato simplificado
                    df_previsao = previsor.obter_dados_previsao(previsao)
                    previsoes[nome_indicador] = df_previsao
                    
                    logger.info(f"Previsão gerada para {nome_indicador}: {len(df_previsao)} registros")
                else:
                    logger.warning(f"Falha ao gerar previsão para {nome_indicador}")
            else:
                logger.warning(f"Falha ao treinar modelo para {nome_indicador}")
                
        except Exception as e:
            logger.error(f"Erro ao processar previsão para {nome_indicador}: {str(e)}")
    
    return previsoes


# Função para execução direta do módulo
def main():
    """Função principal para execução direta do módulo."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Criar dados de exemplo
    datas = pd.date_range(start='2020-01-01', periods=36, freq='M')
    valores = np.random.normal(100, 10, 36) + np.linspace(0, 20, 36)  # Tendência crescente
    
    # Criar DataFrame
    df = pd.DataFrame({'data': datas, 'valor': valores})
    
    # Criar previsor
    previsor = PrevisorSeriesTemporal(horizonte_anos=2)
    
    # Preparar dados
    df_preparado = previsor.preparar_dados(df)
    
    # Treinar modelo
    sucesso = previsor.treinar(df_preparado)
    
    if sucesso:
        # Gerar previsão
        previsao = previsor.prever()
        
        if previsao is not None:
            # Obter dados de previsão
            df_previsao = previsor.obter_dados_previsao(previsao)
            
            # Exibir resultados
            logger.info(f"Previsão gerada: {len(df_previsao)} registros")
            logger.info(f"Último valor histórico: {df_previsao[df_previsao['tipo'] == 'histórico']['valor'].iloc[-1]:.2f}")
            logger.info(f"Último valor previsto: {df_previsao[df_previsao['tipo'] == 'previsão']['valor'].iloc[-1]:.2f}")
            
            # Avaliar modelo
            metricas = previsor.avaliar_modelo()
            logger.info(f"Métricas de avaliação: {metricas}")


# Executar se for o módulo principal
if __name__ == "__main__":
    main()
