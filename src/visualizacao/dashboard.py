"""
Módulo principal do dashboard interativo de indicadores econômicos brasileiros.

Este módulo implementa o dashboard interativo com visualizações, filtros,
comparações e projeções para indicadores econômicos brasileiros.
"""

import os
import sys
import json
import logging
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple

# Adicionar diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar módulos do projeto
try:
    from src.dados.extratores.bcb import ExtratorBCB
    from src.dados.extratores.ibge import ExtratorIBGE
    from src.dados.processadores.previsao import PrevisorSeriesTemporal, gerar_previsoes_para_indicadores
    from src.dados.processadores.eventos import DetectorEventos
    from src.visualizacao.componentes.exibidores import ExibidorMetricas, ExibidorGraficos
    from src.visualizacao.componentes.exportadores import Exportador
    from src.utils.configuracao import obter_configuracao
except ImportError as e:
    st.error(f"Erro ao importar módulos: {str(e)}")
    st.info("Verifique se todos os arquivos do projeto estão presentes e se o ambiente está configurado corretamente.")
    import sys
    sys.exit(1)

# Configuração de logging
logger = logging.getLogger(__name__)

# Configurar página
st.set_page_config(
    page_title="Dashboard de Indicadores Socioeconômicos Brasileiros",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuração global
try:
    config = obter_configuracao()
except Exception as e:
    logger.error(f"Erro ao obter configuração: {str(e)}")
    config = {
        "caminhos": {
            "diretorio_dados": "data",
            "diretorio_icones": "assets/icones"
        }
    }

# Diretório de dados
DIRETORIO_DADOS = config.get("caminhos", {}).get("diretorio_dados", "data")

# Diretório de ícones
DIRETORIO_ICONES = config.get("caminhos", {}).get("diretorio_icones", "assets/icones")

# Arquivo para armazenar a data da última atualização
ARQUIVO_ULTIMA_ATUALIZACAO = os.path.join(DIRETORIO_DADOS, "ultima_atualizacao.json")

# Função para salvar a data da última atualização
def salvar_data_atualizacao():
    """
    Salva a data e hora da última atualização dos dados.
    """
    try:
        data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Criar diretório de dados se não existir
        os.makedirs(DIRETORIO_DADOS, exist_ok=True)
        
        # Salvar em arquivo JSON
        with open(ARQUIVO_ULTIMA_ATUALIZACAO, 'w', encoding='utf-8') as f:
            json.dump({"ultima_atualizacao": data_atual}, f)
        
        return data_atual
    except Exception as e:
        logger.error(f"Erro ao salvar data de atualização: {str(e)}")
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

# Função para carregar a data da última atualização
def carregar_data_atualizacao():
    """
    Carrega a data e hora da última atualização dos dados.
    
    Returns:
        String com a data e hora ou "Nunca atualizado" se não houver registro
    """
    try:
        if os.path.exists(ARQUIVO_ULTIMA_ATUALIZACAO):
            try:
                with open(ARQUIVO_ULTIMA_ATUALIZACAO, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    return dados.get("ultima_atualizacao", "Nunca atualizado")
            except Exception as e:
                logger.error(f"Erro ao carregar data de atualização: {str(e)}")
                return "Nunca atualizado"
        else:
            return "Nunca atualizado"
    except Exception as e:
        logger.error(f"Erro ao verificar arquivo de atualização: {str(e)}")
        return "Nunca atualizado"

# Função para carregar dados
def carregar_dados() -> Dict[str, pd.DataFrame]:
    """
    Carrega todos os dados disponíveis.
    
    Returns:
        Dicionário com DataFrames dos indicadores
    """
    logger.info("Carregando dados dos indicadores")
    
    # Inicializar dicionário com DataFrames vazios para todos os indicadores
    dados = {
        'pib': pd.DataFrame(),
        'desemprego': pd.DataFrame(),
        'deficit_primario': pd.DataFrame(),
        'iof': pd.DataFrame(),
        'ipca': pd.DataFrame(),
        'cambio': pd.DataFrame(),
        'selic': pd.DataFrame()
    }
    
    try:
        # Verificar se diretório de dados existe
        if not os.path.exists(DIRETORIO_DADOS):
            logger.warning(f"Diretório de dados não encontrado: {DIRETORIO_DADOS}")
            os.makedirs(DIRETORIO_DADOS, exist_ok=True)
            return dados
        
        # Mapear arquivos de dados para identificadores
        mapeamento_arquivos = {
            'pib': 'pib.json',
            'desemprego': 'desemprego.json',
            'deficit_primario': 'deficit_primario.json',
            'iof': 'arrecadacao_iof.json',
            'ipca': 'ipca.json',
            'cambio': 'cambio_ptax_venda.json',
            'selic': 'selic.json'
        }
        
        # Carregar cada arquivo
        for id_indicador, nome_arquivo in mapeamento_arquivos.items():
            caminho_arquivo = os.path.join(DIRETORIO_DADOS, nome_arquivo)
            
            if os.path.exists(caminho_arquivo):
                try:
                    # Carregar dados do arquivo JSON
                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        dados_json = json.load(f)
                    
                    # Converter para DataFrame
                    df = pd.DataFrame(dados_json)
                    
                    # Converter coluna de data para datetime
                    if 'data' in df.columns:
                        df['data'] = pd.to_datetime(df['data'], errors='coerce')
                        # Remover linhas com datas inválidas
                        df = df.dropna(subset=['data'])
                    
                    # Adicionar ao dicionário
                    dados[id_indicador] = df
                    
                    logger.info(f"Dados carregados para {id_indicador}: {len(df)} registros")
                    
                except Exception as e:
                    logger.error(f"Erro ao carregar dados de {id_indicador}: {str(e)}")
                    # Manter DataFrame vazio para este indicador
            else:
                logger.warning(f"Arquivo não encontrado para {id_indicador}: {caminho_arquivo}")
                # DataFrame vazio já inicializado
    except Exception as e:
        logger.error(f"Erro ao carregar dados: {str(e)}")
    
    return dados

# Função para atualizar dados
def atualizar_dados() -> Dict[str, pd.DataFrame]:
    """
    Atualiza todos os dados dos indicadores.
    
    Returns:
        Dicionário com DataFrames atualizados
    """
    logger.info("Atualizando dados dos indicadores")
    
    # Inicializar dicionário com DataFrames vazios para todos os indicadores
    dados = {
        'pib': pd.DataFrame(),
        'desemprego': pd.DataFrame(),
        'deficit_primario': pd.DataFrame(),
        'iof': pd.DataFrame(),
        'ipca': pd.DataFrame(),
        'cambio': pd.DataFrame(),
        'selic': pd.DataFrame()
    }
    
    try:
        # Criar diretório de dados se não existir
        os.makedirs(DIRETORIO_DADOS, exist_ok=True)
        
        # Extrair dados do BCB
        try:
            # Criar extrator BCB
            extrator_bcb = ExtratorBCB(diretorio_saida=DIRETORIO_DADOS)
            
            # Extrair dados
            resultados_bcb = extrator_bcb.extrair_todas_series()
            logger.info(f"Resultados da extração BCB: {resultados_bcb}")
            
            # Carregar dados extraídos
            for nome_serie, sucesso in resultados_bcb.items():
                if sucesso:
                    try:
                        # Determinar o ID do indicador com base no nome da série
                        id_indicador = None
                        if nome_serie == 'ipca':
                            id_indicador = 'ipca'
                        elif nome_serie == 'selic':
                            id_indicador = 'selic'
                        elif nome_serie == 'cambio_ptax_venda':
                            id_indicador = 'cambio'
                        elif nome_serie == 'deficit_primario':
                            id_indicador = 'deficit_primario'
                        elif nome_serie == 'arrecadacao_iof':
                            id_indicador = 'iof'
                        
                        if id_indicador:
                            # Carregar dados do arquivo
                            caminho_arquivo = os.path.join(DIRETORIO_DADOS, f"{nome_serie}.json")
                            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                                dados_json = json.load(f)
                            
                            # Converter para DataFrame
                            df = pd.DataFrame(dados_json)
                            
                            # Converter coluna de data para datetime
                            if 'data' in df.columns:
                                df['data'] = pd.to_datetime(df['data'], errors='coerce')
                                # Remover linhas com datas inválidas
                                df = df.dropna(subset=['data'])
                            
                            # Adicionar ao dicionário
                            dados[id_indicador] = df
                            
                            logger.info(f"Dados atualizados para {id_indicador}: {len(df)} registros")
                    except Exception as e:
                        logger.error(f"Erro ao processar dados extraídos para {nome_serie}: {str(e)}")
            
            logger.info("Dados do BCB atualizados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar dados do BCB: {str(e)}")
        
        # Extrair dados do IBGE
        try:
            # Criar extrator IBGE
            extrator_ibge = ExtratorIBGE(diretorio_dados=DIRETORIO_DADOS)
            
            # Extrair PIB
            try:
                df_pib = extrator_ibge.extrair_pib()
                if not df_pib.empty:
                    dados['pib'] = df_pib
                    logger.info(f"Dados do PIB atualizados: {len(df_pib)} registros")
            except Exception as e:
                logger.error(f"Erro ao extrair dados do PIB: {str(e)}")
            
            # Extrair Desemprego
            try:
                df_desemprego = extrator_ibge.extrair_desemprego()
                if not df_desemprego.empty:
                    dados['desemprego'] = df_desemprego
                    logger.info(f"Dados de desemprego atualizados: {len(df_desemprego)} registros")
            except Exception as e:
                logger.error(f"Erro ao extrair dados de desemprego: {str(e)}")
            
            logger.info("Dados do IBGE atualizados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar dados do IBGE: {str(e)}")
        
        # Salvar data da última atualização
        salvar_data_atualizacao()
    except Exception as e:
        logger.error(f"Erro ao atualizar dados: {str(e)}")
    
    return dados

# Função para detectar eventos em indicadores
def detectar_eventos_indicadores(dados_indicadores: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Detecta eventos significativos em todos os indicadores.
    
    Args:
        dados_indicadores: Dicionário com DataFrames dos indicadores
        
    Returns:
        Dicionário com DataFrames dos eventos detectados
    """
    logger.info("Detectando eventos nos indicadores")
    
    eventos = {}
    
    try:
        detector = DetectorEventos()
        
        for nome_indicador, df in dados_indicadores.items():
            if df.empty:
                logger.warning(f"Dados vazios para {nome_indicador}, pulando detecção de eventos")
                continue
            
            try:
                # Detectar eventos
                df_eventos = detector.detectar_eventos(df)
                
                if not df_eventos.empty:
                    eventos[nome_indicador] = df_eventos
                    logger.info(f"Eventos detectados para {nome_indicador}: {len(df_eventos)}")
                else:
                    logger.info(f"Nenhum evento significativo detectado para {nome_indicador}")
                    
            except Exception as e:
                logger.error(f"Erro ao detectar eventos para {nome_indicador}: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao inicializar detector de eventos: {str(e)}")
    
    return eventos

# Função para verificar se um DataFrame é válido e tem as colunas necessárias
def verificar_dataframe(df: Optional[pd.DataFrame], colunas_necessarias: List[str] = None) -> bool:
    """
    Verifica se um DataFrame é válido e contém as colunas necessárias.
    
    Args:
        df: DataFrame a ser verificado
        colunas_necessarias: Lista de colunas que devem estar presentes
        
    Returns:
        True se o DataFrame for válido e contiver as colunas necessárias, False caso contrário
    """
    # Verificar se o DataFrame existe e não está vazio
    if df is None or df.empty:
        return False
    
    # Se não houver colunas específicas para verificar, considerar válido
    if not colunas_necessarias:
        return True
    
    # Verificar se todas as colunas necessárias estão presentes
    return all(coluna in df.columns for coluna in colunas_necessarias)

# Função para obter coluna de valor em um DataFrame com tratamento ultra-robusto
def obter_coluna_valor(df: Optional[pd.DataFrame]) -> Optional[str]:
    """
    Determina a coluna de valor em um DataFrame com tratamento ultra-robusto de erros.
    
    Args:
        df: DataFrame a ser analisado
        
    Returns:
        Nome da coluna de valor ou None se não encontrada
    """
    # Verificar se o DataFrame existe e não está vazio
    if df is None or df.empty:
        return None
    
    try:
        # Lista de possíveis nomes de colunas de valor em ordem de prioridade
        colunas_possiveis = ['valor', 'deficit', 'iof', 'yhat', 'projecao']
        
        # Verificar cada coluna possível
        for coluna in colunas_possiveis:
            if coluna in df.columns:
                return coluna
        
        # Se nenhuma das colunas específicas for encontrada, procurar qualquer coluna numérica que não seja 'data'
        colunas_numericas = []
        for col in df.columns:
            if col != 'data':
                try:
                    # Verificar se a coluna é numérica
                    if pd.api.types.is_numeric_dtype(df[col]):
                        colunas_numericas.append(col)
                except:
                    # Ignorar erros ao verificar o tipo da coluna
                    pass
        
        if colunas_numericas:
            return colunas_numericas[0]
    except Exception as e:
        logger.error(f"Erro ao determinar coluna de valor: {str(e)}")
    
    return None

# Função para obter valor seguro de um DataFrame
def obter_valor_seguro(df: Optional[pd.DataFrame], coluna: str, indice: int = -1, valor_padrao: Any = None) -> Any:
    """
    Obtém um valor de um DataFrame de forma segura, com tratamento de erros.
    
    Args:
        df: DataFrame de origem
        coluna: Nome da coluna
        indice: Índice da linha (padrão: -1, última linha)
        valor_padrao: Valor a retornar em caso de erro
        
    Returns:
        Valor obtido ou valor_padrao em caso de erro
    """
    try:
        # Verificar se o DataFrame existe e não está vazio
        if df is None or df.empty:
            return valor_padrao
        
        # Verificar se a coluna existe
        if coluna not in df.columns:
            return valor_padrao
        
        # Verificar se o índice é válido
        if indice >= len(df) or indice < -len(df):
            return valor_padrao
        
        # Obter o valor
        valor = df.iloc[indice][coluna]
        
        # Verificar se o valor é válido
        if pd.isna(valor):
            return valor_padrao
        
        return valor
    except Exception as e:
        logger.error(f"Erro ao obter valor seguro: {str(e)}")
        return valor_padrao

# Função para exibir projeções com tratamento ultra-robusto de erros
def exibir_projecoes_robusta(id_indicador_prev, projecoes_indicadores, dados_filtrados, config_indicadores):
    """
    Exibe projeções para um indicador com tratamento ultra-robusto de erros.
    
    Args:
        id_indicador_prev: ID do indicador para projeção
        projecoes_indicadores: Dicionário com DataFrames de projeções
        dados_filtrados: Dicionário com DataFrames de dados históricos
        config_indicadores: Configuração dos indicadores
    """
    try:
        # Verificar se o indicador existe na configuração
        if id_indicador_prev not in config_indicadores:
            st.info("Indicador não encontrado na configuração.")
            return
        
        # Obter configuração do indicador
        config_ind = config_indicadores[id_indicador_prev]
        
        # Verificar se há projeções para o indicador selecionado
        if id_indicador_prev not in projecoes_indicadores or projecoes_indicadores[id_indicador_prev] is None or projecoes_indicadores[id_indicador_prev].empty:
            st.info(f"Não foi possível gerar projeções para {config_ind['nome']}. Verifique se há dados históricos suficientes.")
            return
        
        # Exibir gráfico de projeção
        st.subheader(f"Projeção de {config_ind['nome']} para os próximos 2 anos")
        
        # Obter DataFrames com tratamento seguro
        df_historico = dados_filtrados.get(id_indicador_prev, pd.DataFrame()).copy() if id_indicador_prev in dados_filtrados else pd.DataFrame()
        df_projecao = projecoes_indicadores.get(id_indicador_prev, pd.DataFrame()).copy() if id_indicador_prev in projecoes_indicadores else pd.DataFrame()
        
        # Verificar se os DataFrames são válidos
        if df_projecao.empty:
            st.warning("Não há dados de projeção disponíveis para este indicador.")
            return
        
        # Verificar e mapear colunas do DataFrame de projeção
        colunas_data = ['ds', 'data']  # Possíveis nomes para coluna de data
        colunas_valor = ['yhat', 'valor', 'projecao']  # Possíveis nomes para coluna de valor
        colunas_limite_inf = ['yhat_lower', 'limite_inferior']  # Possíveis nomes para limite inferior
        colunas_limite_sup = ['yhat_upper', 'limite_superior']  # Possíveis nomes para limite superior
        
        # Encontrar coluna de data
        coluna_data_proj = None
        for col in colunas_data:
            if col in df_projecao.columns:
                coluna_data_proj = col
                break
        
        # Encontrar coluna de valor
        coluna_valor_proj = None
        for col in colunas_valor:
            if col in df_projecao.columns:
                coluna_valor_proj = col
                break
        
        # Encontrar coluna de limite inferior
        coluna_limite_inf = None
        for col in colunas_limite_inf:
            if col in df_projecao.columns:
                coluna_limite_inf = col
                break
        
        # Encontrar coluna de limite superior
        coluna_limite_sup = None
        for col in colunas_limite_sup:
            if col in df_projecao.columns:
                coluna_limite_sup = col
                break
        
        # Verificar se encontrou as colunas necessárias
        if not coluna_data_proj or not coluna_valor_proj:
            # Tentar criar colunas padrão se não encontrou
            if not coluna_data_proj and 'data' not in df_projecao.columns and len(df_projecao) > 0:
                # Criar coluna de data artificial
                datas = [datetime.now() + timedelta(days=i*30) for i in range(len(df_projecao))]
                df_projecao['data'] = datas
                coluna_data_proj = 'data'
                st.info("Criada coluna de data artificial para projeções.")
            
            if not coluna_valor_proj:
                # Tentar encontrar qualquer coluna numérica
                for col in df_projecao.columns:
                    if col != coluna_data_proj:
                        try:
                            if pd.api.types.is_numeric_dtype(df_projecao[col]):
                                coluna_valor_proj = col
                                break
                        except:
                            pass
            
            # Verificar novamente
            if not coluna_data_proj or not coluna_valor_proj:
                st.warning(f"Formato de dados de projeção incompatível. Colunas disponíveis: {', '.join(df_projecao.columns)}")
                return
        
        # Determinar colunas de valor no histórico
        coluna_valor_hist = obter_coluna_valor(df_historico)
        
        # Criar figura
        fig = go.Figure()
        
        # Adicionar dados históricos
        if not df_historico.empty and coluna_valor_hist and 'data' in df_historico.columns:
            try:
                fig.add_trace(go.Scatter(
                    x=df_historico['data'],
                    y=df_historico[coluna_valor_hist],
                    name="Dados Históricos",
                    line=dict(color=config_ind['cor'])
                ))
            except Exception as e:
                logger.error(f"Erro ao adicionar dados históricos ao gráfico: {str(e)}")
                st.warning("Não foi possível incluir dados históricos no gráfico.")
        
        # Adicionar projeção
        try:
            fig.add_trace(go.Scatter(
                x=df_projecao[coluna_data_proj],
                y=df_projecao[coluna_valor_proj],
                name="Projeção",
                line=dict(color='rgba(0, 0, 255, 0.8)', dash='dash')
            ))
        except Exception as e:
            logger.error(f"Erro ao adicionar projeção ao gráfico: {str(e)}")
            st.warning("Não foi possível incluir a linha de projeção no gráfico.")
            return
        
        # Adicionar intervalo de confiança se disponível
        if coluna_limite_inf and coluna_limite_sup:
            try:
                fig.add_trace(go.Scatter(
                    x=df_projecao[coluna_data_proj].tolist() + df_projecao[coluna_data_proj].tolist()[::-1],
                    y=df_projecao[coluna_limite_sup].tolist() + df_projecao[coluna_limite_inf].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(0, 0, 255, 0.1)',
                    line=dict(color='rgba(255, 255, 255, 0)'),
                    name="Intervalo de Confiança (95%)"
                ))
            except Exception as e:
                logger.error(f"Erro ao adicionar intervalo de confiança ao gráfico: {str(e)}")
        
        # Configurar layout
        fig.update_layout(
            title=f"Projeção de {config_ind['nome']} para os próximos 2 anos",
            xaxis=dict(title="Data"),
            yaxis=dict(title=f"{config_ind['nome']} ({config_ind['unidade']})"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # Exibir gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Exibir tabela de projeções
        st.subheader("Valores Projetados")
        
        try:
            # Criar tabela de projeções
            colunas_tabela = [coluna_data_proj, coluna_valor_proj]
            if coluna_limite_inf:
                colunas_tabela.append(coluna_limite_inf)
            if coluna_limite_sup:
                colunas_tabela.append(coluna_limite_sup)
            
            # Verificar se todas as colunas existem
            colunas_existentes = [col for col in colunas_tabela if col in df_projecao.columns]
            
            if colunas_existentes:
                df_tabela = df_projecao[colunas_existentes].copy()
                
                # Renomear colunas para exibição
                mapeamento_colunas = {}
                if coluna_data_proj in colunas_existentes:
                    mapeamento_colunas[coluna_data_proj] = 'Data'
                if coluna_valor_proj in colunas_existentes:
                    mapeamento_colunas[coluna_valor_proj] = 'Projeção'
                if coluna_limite_inf in colunas_existentes:
                    mapeamento_colunas[coluna_limite_inf] = 'Limite Inferior'
                if coluna_limite_sup in colunas_existentes:
                    mapeamento_colunas[coluna_limite_sup] = 'Limite Superior'
                
                df_tabela = df_tabela.rename(columns=mapeamento_colunas)
                
                # Formatar valores
                for col in ['Projeção', 'Limite Inferior', 'Limite Superior']:
                    if col in df_tabela.columns:
                        try:
                            df_tabela[col] = df_tabela[col].apply(
                                lambda x: config_ind['formato'].format(x) if pd.notnull(x) else 'N/A'
                            )
                        except Exception as e:
                            logger.error(f"Erro ao formatar coluna {col}: {str(e)}")
                            # Manter valores originais em caso de erro
                
                # Formatar datas
                if 'Data' in df_tabela.columns:
                    try:
                        if pd.api.types.is_datetime64_any_dtype(df_tabela['Data']):
                            df_tabela['Data'] = df_tabela['Data'].dt.strftime('%d/%m/%Y')
                        elif isinstance(df_tabela['Data'].iloc[0], str):
                            # Tentar converter para datetime e depois formatar
                            df_tabela['Data'] = pd.to_datetime(df_tabela['Data'], errors='coerce').dt.strftime('%d/%m/%Y')
                    except Exception as e:
                        logger.error(f"Erro ao formatar datas: {str(e)}")
                        # Manter valores originais em caso de erro
                
                # Ordenar por data (mais próxima primeiro)
                try:
                    if 'Data' in df_tabela.columns:
                        df_tabela = df_tabela.sort_values('Data')
                except Exception as e:
                    logger.error(f"Erro ao ordenar tabela: {str(e)}")
                
                # Exibir tabela
                st.dataframe(df_tabela, use_container_width=True)
            else:
                st.warning("Não foi possível criar tabela de projeções devido à falta de colunas necessárias.")
        except Exception as e:
            logger.error(f"Erro ao exibir tabela de projeções: {str(e)}")
            st.warning("Não foi possível exibir a tabela de projeções devido a um erro no formato dos dados.")
        
        # Exibir informações sobre a metodologia
        with st.expander("Sobre a Metodologia de Projeção"):
            st.markdown("""
            ### Metodologia de Projeção
            
            As projeções são geradas utilizando o modelo Prophet, desenvolvido pelo Facebook Research. Este modelo é especialmente adequado para séries temporais com forte sazonalidade e tendências não-lineares.
            
            **Características do modelo:**
            - Decomposição da série em tendência, sazonalidade e componente de feriados
            - Detecção automática de mudanças na tendência
            - Tratamento robusto de outliers
            - Intervalos de confiança para quantificar a incerteza
            
            **Limitações:**
            - As projeções são baseadas apenas no comportamento histórico da série
            - Eventos externos não capturados nos dados históricos não são considerados
            - A precisão diminui à medida que o horizonte de previsão aumenta
            
            Para mais informações, consulte a [documentação do Prophet](https://facebook.github.io/prophet/).
            """)
    except Exception as e:
        logger.error(f"Erro ao exibir projeções: {str(e)}")
        st.warning(f"Ocorreu um erro ao exibir as projeções. Por favor, tente novamente mais tarde.")

# Função principal
def main():
    """Função principal do dashboard."""
    try:
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/dashboard.log"),
                logging.StreamHandler()
            ]
        )
        
        # Criar diretório de logs se não existir
        os.makedirs("logs", exist_ok=True)
        
        # Título e descrição
        st.title("Dashboard de Indicadores Socioeconômicos Brasileiros")
        st.markdown("""
        Este dashboard apresenta indicadores econômicos brasileiros, incluindo PIB, IPCA, desemprego, 
        câmbio, arrecadação de IOF e déficit primário. Explore os dados, compare indicadores e 
        visualize projeções futuras.
        """)
        
        # Sidebar
        with st.sidebar:
            st.header("Filtros e Configurações")
            
            # Botão para atualizar dados
            if st.button("🔄 Atualizar Dados", help="Busca dados atualizados das fontes oficiais"):
                with st.spinner("Atualizando dados..."):
                    try:
                        dados_indicadores = atualizar_dados()
                        st.session_state['dados_indicadores'] = dados_indicadores
                        st.session_state['dados_atualizados'] = True
                        st.success("Dados atualizados com sucesso!")
                    except Exception as e:
                        logger.error(f"Erro ao atualizar dados: {str(e)}")
                        st.error(f"Erro ao atualizar dados: {str(e)}")
            
            # Exibir data da última atualização
            ultima_atualizacao = carregar_data_atualizacao()
            st.caption(f"**Última atualização:** {ultima_atualizacao}")
            
            # Filtro de período
            st.subheader("Período")
            
            # Determinar anos disponíveis
            anos_disponiveis = []
            if 'dados_indicadores' in st.session_state:
                for df in st.session_state['dados_indicadores'].values():
                    if not df.empty and 'data' in df.columns:
                        try:
                            anos = df['data'].dt.year.unique().tolist()
                            anos_disponiveis.extend(anos)
                        except Exception as e:
                            logger.error(f"Erro ao extrair anos: {str(e)}")
            
            anos_disponiveis = sorted(list(set(anos_disponiveis)))
            
            if not anos_disponiveis:
                anos_disponiveis = list(range(2010, datetime.now().year + 1))
            
            # Slider para seleção de anos
            try:
                ano_min, ano_max = st.select_slider(
                    "Selecione o intervalo de anos:",
                    options=anos_disponiveis,
                    value=(min(anos_disponiveis), max(anos_disponiveis))
                )
                
                anos_selecionados = list(range(ano_min, ano_max + 1))
            except Exception as e:
                logger.error(f"Erro ao criar slider de anos: {str(e)}")
                # Fallback para anos padrão
                anos_selecionados = list(range(2010, datetime.now().year + 1))
                st.warning("Erro ao criar seletor de anos. Usando intervalo padrão.")
            
            # Filtro de indicadores
            st.subheader("Indicadores")
            
            # Configuração dos indicadores
            config_indicadores = {
                'pib': {
                    'nome': 'PIB',
                    'descricao': 'Produto Interno Bruto',
                    'fonte': 'IBGE',
                    'unidade': 'R$ bilhões',
                    'formato': '{:.2f}',
                    'icone': 'pib.png',
                    'cor': '#1f77b4'
                },
                'desemprego': {
                    'nome': 'Taxa de Desemprego',
                    'descricao': 'Taxa de Desemprego (PNAD Contínua)',
                    'fonte': 'IBGE',
                    'unidade': '%',
                    'formato': '{:.2f}%',
                    'icone': 'desemprego.png',
                    'cor': '#d62728'
                },
                'deficit_primario': {
                    'nome': 'Déficit Primário',
                    'descricao': 'Resultado Primário do Governo Central',
                    'fonte': 'Tesouro Nacional/BCB',
                    'unidade': 'R$ milhões',
                    'formato': '{:.2f}',
                    'icone': 'meta.png',
                    'cor': '#ff7f0e'
                },
                'iof': {
                    'nome': 'Arrecadação IOF',
                    'descricao': 'Arrecadação do Imposto sobre Operações Financeiras',
                    'fonte': 'Receita Federal/BCB',
                    'unidade': 'R$ milhões',
                    'formato': '{:.2f}',
                    'icone': 'mercado-de-acoes.png',
                    'cor': '#2ca02c'
                },
                'ipca': {
                    'nome': 'IPCA',
                    'descricao': 'Índice Nacional de Preços ao Consumidor Amplo',
                    'fonte': 'IBGE/BCB',
                    'unidade': '% a.m.',
                    'formato': '{:.2f}%',
                    'icone': 'inflacao.png',
                    'cor': '#9467bd'
                },
                'cambio': {
                    'nome': 'Câmbio (USD/BRL)',
                    'descricao': 'Taxa de Câmbio - Dólar americano (venda)',
                    'fonte': 'BCB',
                    'unidade': 'R$',
                    'formato': 'R$ {:.2f}',
                    'icone': 'cambio.png',
                    'cor': '#8c564b'
                },
                'selic': {
                    'nome': 'Taxa Selic',
                    'descricao': 'Taxa básica de juros da economia',
                    'fonte': 'BCB',
                    'unidade': '% a.a.',
                    'formato': '{:.2f}%',
                    'icone': 'selic.png',
                    'cor': '#e377c2'
                }
            }
            
            # Seleção de indicadores para visualização
            try:
                indicadores_selecionados = st.multiselect(
                    "Selecione os indicadores para visualização:",
                    options=list(config_indicadores.keys()),
                    default=['pib', 'desemprego', 'ipca'],
                    format_func=lambda x: config_indicadores[x]['nome']
                )
            except Exception as e:
                logger.error(f"Erro ao criar seletor de indicadores: {str(e)}")
                # Fallback para indicadores padrão
                indicadores_selecionados = ['pib', 'desemprego', 'ipca']
                st.warning("Erro ao criar seletor de indicadores. Usando seleção padrão.")
            
            # Opções adicionais
            st.subheader("Opções")
            
            # Opção para mostrar eventos significativos
            try:
                mostrar_eventos = st.checkbox("Mostrar eventos significativos", value=True)
            except Exception as e:
                logger.error(f"Erro ao criar checkbox de eventos: {str(e)}")
                mostrar_eventos = True
            
            # Opção para mostrar projeções
            try:
                mostrar_projecoes = st.checkbox("Mostrar projeções futuras", value=True)
            except Exception as e:
                logger.error(f"Erro ao criar checkbox de projeções: {str(e)}")
                mostrar_projecoes = True
        
        # Carregar dados se não estiverem na sessão
        if 'dados_indicadores' not in st.session_state:
            with st.spinner("Carregando dados..."):
                try:
                    dados_indicadores = carregar_dados()
                    st.session_state['dados_indicadores'] = dados_indicadores
                except Exception as e:
                    logger.error(f"Erro ao carregar dados: {str(e)}")
                    dados_indicadores = {
                        'pib': pd.DataFrame(),
                        'desemprego': pd.DataFrame(),
                        'deficit_primario': pd.DataFrame(),
                        'iof': pd.DataFrame(),
                        'ipca': pd.DataFrame(),
                        'cambio': pd.DataFrame(),
                        'selic': pd.DataFrame()
                    }
                    st.session_state['dados_indicadores'] = dados_indicadores
                    st.error(f"Erro ao carregar dados: {str(e)}")
        else:
            dados_indicadores = st.session_state['dados_indicadores']
        
        # Filtrar dados pelo período selecionado
        dados_filtrados = {}
        try:
            for id_indicador, df in dados_indicadores.items():
                if not df.empty and 'data' in df.columns:
                    try:
                        # Adicionar coluna de ano
                        df['ano'] = df['data'].dt.year
                        
                        # Filtrar por anos selecionados
                        df_filtrado = df[df['ano'].isin(anos_selecionados)]
                        
                        # Remover coluna de ano (temporária)
                        df_filtrado = df_filtrado.drop(columns=['ano'])
                        
                        dados_filtrados[id_indicador] = df_filtrado
                    except Exception as e:
                        logger.error(f"Erro ao filtrar dados de {id_indicador}: {str(e)}")
                        dados_filtrados[id_indicador] = df
                else:
                    dados_filtrados[id_indicador] = df
        except Exception as e:
            logger.error(f"Erro ao filtrar dados por período: {str(e)}")
            dados_filtrados = dados_indicadores.copy()
        
        # Detectar eventos se solicitado
        eventos_indicadores = {}
        if mostrar_eventos:
            try:
                eventos_indicadores = detectar_eventos_indicadores(dados_filtrados)
            except Exception as e:
                logger.error(f"Erro ao detectar eventos: {str(e)}")
                st.warning(f"Não foi possível detectar eventos: {str(e)}")
        
        # Gerar projeções se solicitado
        projecoes_indicadores = {}
        if mostrar_projecoes:
            try:
                projecoes_indicadores = gerar_previsoes_para_indicadores(dados_filtrados)
            except Exception as e:
                logger.error(f"Erro ao gerar projeções: {str(e)}")
                st.warning("Não foi possível gerar projeções. Verifique os dados e tente novamente.")
        
        # Inicializar componentes de visualização
        try:
            exibidor_metricas = ExibidorMetricas(diretorio_icones=DIRETORIO_ICONES)
            exibidor_graficos = ExibidorGraficos()
            exportador = Exportador()
        except Exception as e:
            logger.error(f"Erro ao inicializar componentes de visualização: {str(e)}")
            st.error(f"Erro ao inicializar componentes de visualização: {str(e)}")
            return
        
        # Criar abas
        try:
            tab_visao_geral, tab_detalhes, tab_comparativo, tab_previsoes, tab_exportar = st.tabs([
                "Visão Geral", "Detalhes", "Comparativo", "Previsões", "Exportar Dados"
            ])
        except Exception as e:
            logger.error(f"Erro ao criar abas: {str(e)}")
            st.error(f"Erro ao criar abas: {str(e)}")
            return
        
        # Aba de Visão Geral
        with tab_visao_geral:
            try:
                # Banner (tamanho reduzido)
                banner_path = os.path.join(DIRETORIO_ICONES, "banner 2.png")
                if os.path.exists(banner_path):
                    # Exibir banner com tamanho reduzido
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col2:
                        st.image(banner_path, use_container_width=True)
                
                # Métricas principais
                st.header("Últimos Valores Registrados")
                
                # Verificar se há dados para exibir métricas
                tem_dados = False
                for df in dados_filtrados.values():
                    if not df.empty:
                        tem_dados = True
                        break
                
                if tem_dados:
                    # Criar colunas para métricas
                    try:
                        cols = st.columns(len(indicadores_selecionados) if indicadores_selecionados else 1)
                    except Exception as e:
                        logger.error(f"Erro ao criar colunas para métricas: {str(e)}")
                        cols = [st.container()]
                    
                    # Exibir métricas para cada indicador selecionado
                    for i, id_indicador in enumerate(indicadores_selecionados):
                        try:
                            with cols[i % len(cols)]:
                                try:
                                    # Verificar se o indicador existe na configuração
                                    if id_indicador not in config_indicadores:
                                        st.warning(f"Configuração não encontrada para o indicador {id_indicador}")
                                        continue
                                    
                                    # Obter configuração do indicador
                                    config_ind = config_indicadores[id_indicador]
                                    
                                    # Verificar se há dados para o indicador
                                    if id_indicador not in dados_filtrados or dados_filtrados[id_indicador].empty:
                                        st.info(f"Sem dados para {config_ind['nome']}")
                                        continue
                                    
                                    # Exibir ícone se disponível
                                    icone_path = os.path.join(DIRETORIO_ICONES, config_ind['icone'])
                                    if os.path.exists(icone_path):
                                        st.image(icone_path, width=50, use_container_width=False)
                                    
                                    # Obter o DataFrame
                                    df = dados_filtrados[id_indicador]
                                    
                                    # Verificar se o DataFrame tem a coluna 'data'
                                    if 'data' not in df.columns:
                                        st.warning(f"Coluna 'data' não encontrada para {config_ind['nome']}")
                                        continue
                                    
                                    # Determinar a coluna de valor
                                    coluna_valor = obter_coluna_valor(df)
                                    
                                    # Verificar se encontrou uma coluna de valor
                                    if coluna_valor is None:
                                        st.warning(f"Não foi possível determinar a coluna de valor para {config_ind['nome']}")
                                        continue
                                    
                                    # Verificar se há dados
                                    if len(df) == 0:
                                        st.info(f"Sem dados para {config_ind['nome']}")
                                        continue
                                    
                                    # Obter a última linha
                                    try:
                                        ultima_linha = df.iloc[-1]
                                        ultima_data = ultima_linha['data']
                                        
                                        # Obter e formatar o valor
                                        valor = ultima_linha[coluna_valor]
                                        
                                        # Verificar se o valor é válido
                                        if pd.isna(valor):
                                            st.info(f"Valor não disponível para {config_ind['nome']}")
                                            continue
                                        
                                        # Formatar o valor
                                        try:
                                            valor_formatado = config_ind['formato'].format(valor)
                                        except Exception as e:
                                            logger.error(f"Erro ao formatar valor para {id_indicador}: {str(e)}")
                                            valor_formatado = str(valor)
                                        
                                        # Exibir a métrica
                                        st.metric(
                                            label=config_ind['nome'],
                                            value=valor_formatado,
                                            delta=None,
                                            help=f"Última atualização: {ultima_data.strftime('%d/%m/%Y')}"
                                        )
                                        
                                        # Exibir informação adicional
                                        st.caption(f"Unidade: {config_ind['unidade']}")
                                    except Exception as e:
                                        logger.error(f"Erro ao processar última linha para {id_indicador}: {str(e)}")
                                        st.warning(f"Erro ao processar dados para {config_ind['nome']}")
                                except Exception as e:
                                    logger.error(f"Erro ao exibir métrica para {id_indicador}: {str(e)}")
                                    st.warning(f"Erro ao exibir métrica para {id_indicador}")
                        except Exception as e:
                            logger.error(f"Erro ao processar indicador {id_indicador}: {str(e)}")
                else:
                    st.info("Nenhum dado disponível para exibição de métricas.")
                
                # Gráfico principal
                st.header("Visualização Histórica de Indicadores Macroeconômicos")
                
                # Seleção do indicador principal
                try:
                    id_indicador_principal = st.selectbox(
                        "Selecione o indicador principal:",
                        options=indicadores_selecionados if indicadores_selecionados else list(config_indicadores.keys()),
                        format_func=lambda x: config_indicadores[x]['nome']
                    )
                except Exception as e:
                    logger.error(f"Erro ao criar seletor de indicador principal: {str(e)}")
                    # Fallback para primeiro indicador
                    id_indicador_principal = indicadores_selecionados[0] if indicadores_selecionados else list(config_indicadores.keys())[0]
                    st.warning("Erro ao criar seletor de indicador principal. Usando primeiro indicador.")
                
                # Verificar se há dados para o indicador selecionado
                if id_indicador_principal in dados_filtrados and not dados_filtrados[id_indicador_principal].empty:
                    # Obter configuração do indicador
                    config_ind = config_indicadores[id_indicador_principal]
                    
                    # Exibir gráfico
                    try:
                        exibidor_graficos.exibir_serie_temporal(
                            dados_filtrados[id_indicador_principal],
                            f"Evolução de {config_ind['nome']} ({config_ind['unidade']})",
                            config_ind['cor'],
                            mostrar_eventos=mostrar_eventos
                        )
                    except Exception as e:
                        logger.error(f"Erro ao exibir série temporal: {str(e)}")
                        
                        # Implementação de fallback para exibir gráfico
                        try:
                            df = dados_filtrados[id_indicador_principal]
                            
                            # Verificar se o DataFrame tem as colunas necessárias
                            if 'data' not in df.columns:
                                st.warning(f"Coluna 'data' não encontrada para {config_ind['nome']}")
                            else:
                                # Determinar a coluna de valor
                                coluna_valor = obter_coluna_valor(df)
                                
                                if coluna_valor:
                                    # Criar gráfico simples
                                    fig = px.line(
                                        df, 
                                        x='data', 
                                        y=coluna_valor,
                                        title=f"Evolução de {config_ind['nome']} ({config_ind['unidade']})"
                                    )
                                    
                                    # Configurar layout
                                    fig.update_layout(
                                        xaxis_title="Data",
                                        yaxis_title=f"{config_ind['nome']} ({config_ind['unidade']})"
                                    )
                                    
                                    # Exibir gráfico
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning(f"Não foi possível determinar a coluna de valor para {config_ind['nome']}")
                        except Exception as e2:
                            logger.error(f"Erro no fallback para exibir série temporal: {str(e2)}")
                            st.warning(f"Não foi possível exibir o gráfico para {config_ind['nome']}")
                else:
                    st.info(f"Não há dados disponíveis para {config_indicadores[id_indicador_principal]['nome']} no período selecionado.")
            except Exception as e:
                logger.error(f"Erro na aba Visão Geral: {str(e)}")
                st.error(f"Ocorreu um erro na aba Visão Geral: {str(e)}")
        
        # Aba de Detalhes
        with tab_detalhes:
            try:
                st.header("Análise Detalhada por Indicador")
                
                # Seleção do indicador para análise detalhada
                try:
                    id_indicador_detalhes = st.selectbox(
                        "Selecione o indicador para análise detalhada:",
                        options=indicadores_selecionados if indicadores_selecionados else list(config_indicadores.keys()),
                        format_func=lambda x: config_indicadores[x]['nome'],
                        key="detalhes_indicador"
                    )
                except Exception as e:
                    logger.error(f"Erro ao criar seletor de indicador para detalhes: {str(e)}")
                    # Fallback para primeiro indicador
                    id_indicador_detalhes = indicadores_selecionados[0] if indicadores_selecionados else list(config_indicadores.keys())[0]
                    st.warning("Erro ao criar seletor de indicador para detalhes. Usando primeiro indicador.")
                
                # Verificar se o indicador existe na configuração
                if id_indicador_detalhes not in config_indicadores:
                    st.warning(f"Configuração não encontrada para o indicador {id_indicador_detalhes}")
                else:
                    # Obter configuração do indicador
                    config_ind = config_indicadores[id_indicador_detalhes]
                    
                    # Verificar se há dados para o indicador selecionado
                    if id_indicador_detalhes not in dados_filtrados or dados_filtrados[id_indicador_detalhes].empty:
                        st.info(f"Não há dados disponíveis para {config_ind['nome']} no período selecionado.")
                    else:
                        # Exibir estatísticas descritivas
                        st.subheader(f"Estatísticas de {config_ind['nome']}")
                        
                        # Criar colunas para estatísticas e gráfico
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            try:
                                # Exibir estatísticas
                                exibidor_metricas.exibir_estatisticas_indicador(
                                    dados_filtrados[id_indicador_detalhes],
                                    config_ind['formato']
                                )
                            except Exception as e:
                                logger.error(f"Erro ao exibir estatísticas: {str(e)}")
                                
                                # Implementação de fallback para exibir estatísticas
                                try:
                                    df = dados_filtrados[id_indicador_detalhes]
                                    
                                    # Determinar a coluna de valor
                                    coluna_valor = obter_coluna_valor(df)
                                    
                                    if coluna_valor:
                                        # Calcular estatísticas básicas
                                        try:
                                            minimo = df[coluna_valor].min()
                                            maximo = df[coluna_valor].max()
                                            media = df[coluna_valor].mean()
                                            mediana = df[coluna_valor].median()
                                            
                                            # Formatar valores
                                            try:
                                                minimo_fmt = config_ind['formato'].format(minimo)
                                                maximo_fmt = config_ind['formato'].format(maximo)
                                                media_fmt = config_ind['formato'].format(media)
                                                mediana_fmt = config_ind['formato'].format(mediana)
                                            except Exception as e:
                                                logger.error(f"Erro ao formatar estatísticas: {str(e)}")
                                                minimo_fmt = str(minimo)
                                                maximo_fmt = str(maximo)
                                                media_fmt = str(media)
                                                mediana_fmt = str(mediana)
                                            
                                            # Exibir estatísticas
                                            st.metric("Mínimo", minimo_fmt)
                                            st.metric("Máximo", maximo_fmt)
                                            st.metric("Média", media_fmt)
                                            st.metric("Mediana", mediana_fmt)
                                        except Exception as e:
                                            logger.error(f"Erro ao calcular estatísticas: {str(e)}")
                                            st.warning("Erro ao calcular estatísticas")
                                    else:
                                        st.warning(f"Não foi possível determinar a coluna de valor para {config_ind['nome']}")
                                except Exception as e2:
                                    logger.error(f"Erro no fallback para exibir estatísticas: {str(e2)}")
                                    st.warning("Não foi possível exibir estatísticas para este indicador.")
                            
                            # Exibir informações adicionais
                            st.info(f"""
                            **Descrição:** {config_ind['descricao']}
                            
                            **Fonte:** {config_ind['fonte']}
                            
                            **Unidade:** {config_ind['unidade']}
                            """)
                        
                        with col2:
                            # Exibir gráfico de distribuição
                            try:
                                # Determinar a coluna de valor
                                coluna_valor = obter_coluna_valor(dados_filtrados[id_indicador_detalhes])
                                
                                if coluna_valor:
                                    # Criar histograma
                                    fig = px.histogram(
                                        dados_filtrados[id_indicador_detalhes], 
                                        x=coluna_valor,
                                        nbins=20,
                                        title=f"Distribuição de {config_ind['nome']}",
                                        labels={coluna_valor: config_ind['nome']}
                                    )
                                    
                                    # Exibir gráfico
                                    st.plotly_chart(fig, use_container_width=True)
                                else:
                                    st.warning("Não foi possível determinar a coluna de valor para o histograma")
                            except Exception as e:
                                logger.error(f"Erro ao exibir histograma: {str(e)}")
                                st.warning("Erro ao exibir histograma")
                        
                        # Exibir tabela de dados
                        st.subheader(f"Dados de {config_ind['nome']}")
                        
                        try:
                            df = dados_filtrados[id_indicador_detalhes]
                            
                            # Verificar se o DataFrame tem a coluna 'data'
                            if 'data' not in df.columns:
                                st.warning(f"Coluna 'data' não encontrada para {config_ind['nome']}")
                            else:
                                # Determinar a coluna de valor
                                coluna_valor = obter_coluna_valor(df)
                                
                                if coluna_valor:
                                    # Criar tabela simplificada
                                    df_exibicao = df[['data', coluna_valor]].copy()
                                    df_exibicao.columns = ['Data', config_ind['nome']]
                                    
                                    # Formatar valores
                                    try:
                                        df_exibicao[config_ind['nome']] = df_exibicao[config_ind['nome']].apply(
                                            lambda x: config_ind['formato'].format(x) if pd.notnull(x) else 'N/A'
                                        )
                                    except Exception as e:
                                        logger.error(f"Erro ao formatar valores para tabela: {str(e)}")
                                        # Manter valores originais em caso de erro
                                    
                                    # Formatar datas
                                    try:
                                        df_exibicao['Data'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
                                    except Exception as e:
                                        logger.error(f"Erro ao formatar datas para tabela: {str(e)}")
                                        # Manter valores originais em caso de erro
                                    
                                    # Ordenar por data (mais recente primeiro)
                                    try:
                                        df_exibicao = df_exibicao.sort_values('Data', ascending=False)
                                    except Exception as e:
                                        logger.error(f"Erro ao ordenar tabela: {str(e)}")
                                        # Manter ordem original em caso de erro
                                    
                                    # Exibir tabela
                                    st.dataframe(df_exibicao, use_container_width=True)
                                else:
                                    st.warning("Não foi possível determinar a coluna de valor para a tabela")
                        except Exception as e:
                            logger.error(f"Erro ao exibir tabela de dados: {str(e)}")
                            st.warning("Não foi possível exibir a tabela de dados.")
            except Exception as e:
                logger.error(f"Erro na aba Detalhes: {str(e)}")
                st.error(f"Ocorreu um erro na aba Detalhes: {str(e)}")
        
        # Aba de Comparativo
        with tab_comparativo:
            try:
                st.header("Comparativo entre Indicadores")
                
                # Verificar se há pelo menos dois indicadores selecionados
                if len(indicadores_selecionados) < 2:
                    st.warning("Selecione pelo menos dois indicadores para comparação.")
                else:
                    # Seleção dos indicadores para comparação
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        try:
                            id_indicador_comp1 = st.selectbox(
                                "Selecione o primeiro indicador:",
                                options=indicadores_selecionados,
                                format_func=lambda x: config_indicadores[x]['nome'],
                                key="comp_ind1"
                            )
                        except Exception as e:
                            logger.error(f"Erro ao criar seletor do primeiro indicador para comparação: {str(e)}")
                            # Fallback para primeiro indicador
                            id_indicador_comp1 = indicadores_selecionados[0]
                            st.warning("Erro ao criar seletor do primeiro indicador. Usando primeiro indicador selecionado.")
                    
                    with col2:
                        try:
                            # Filtrar para não permitir selecionar o mesmo indicador duas vezes
                            opcoes_restantes = [id for id in indicadores_selecionados if id != id_indicador_comp1]
                            
                            if opcoes_restantes:
                                id_indicador_comp2 = st.selectbox(
                                    "Selecione o segundo indicador:",
                                    options=opcoes_restantes,
                                    format_func=lambda x: config_indicadores[x]['nome'],
                                    key="comp_ind2"
                                )
                            else:
                                st.warning("Não há indicadores adicionais para comparação.")
                                id_indicador_comp2 = None
                        except Exception as e:
                            logger.error(f"Erro ao criar seletor do segundo indicador para comparação: {str(e)}")
                            # Fallback para segundo indicador
                            opcoes_restantes = [id for id in indicadores_selecionados if id != id_indicador_comp1]
                            id_indicador_comp2 = opcoes_restantes[0] if opcoes_restantes else None
                            if id_indicador_comp2:
                                st.warning("Erro ao criar seletor do segundo indicador. Usando segundo indicador disponível.")
                    
                    # Verificar se ambos os indicadores foram selecionados
                    if id_indicador_comp1 is None or id_indicador_comp2 is None:
                        st.warning("Não foi possível selecionar dois indicadores diferentes para comparação.")
                    else:
                        # Verificar se os indicadores existem na configuração
                        if id_indicador_comp1 not in config_indicadores or id_indicador_comp2 not in config_indicadores:
                            st.warning("Configuração não encontrada para um ou ambos os indicadores selecionados.")
                        else:
                            # Obter configurações dos indicadores
                            config_ind1 = config_indicadores[id_indicador_comp1]
                            config_ind2 = config_indicadores[id_indicador_comp2]
                            
                            # Verificar se há dados para os indicadores selecionados
                            if (id_indicador_comp1 not in dados_filtrados or dados_filtrados[id_indicador_comp1].empty or
                                id_indicador_comp2 not in dados_filtrados or dados_filtrados[id_indicador_comp2].empty):
                                st.info("Não há dados disponíveis para um ou ambos os indicadores selecionados no período selecionado.")
                            else:
                                # Verificar se os DataFrames têm a coluna 'data'
                                df1 = dados_filtrados[id_indicador_comp1]
                                df2 = dados_filtrados[id_indicador_comp2]
                                
                                if 'data' not in df1.columns or 'data' not in df2.columns:
                                    st.warning("Coluna 'data' não encontrada para um ou ambos os indicadores.")
                                else:
                                    # Determinar colunas de valor
                                    coluna_valor1 = obter_coluna_valor(df1)
                                    coluna_valor2 = obter_coluna_valor(df2)
                                    
                                    if not coluna_valor1 or not coluna_valor2:
                                        st.warning("Não foi possível determinar as colunas de valor para um ou ambos os indicadores.")
                                    else:
                                        # Exibir gráfico de comparação
                                        st.subheader(f"Comparação: {config_ind1['nome']} vs {config_ind2['nome']}")
                                        
                                        # Criar gráfico de comparação
                                        try:
                                            # Criar figura com dois eixos Y
                                            fig = go.Figure()
                                            
                                            # Adicionar primeira série
                                            fig.add_trace(go.Scatter(
                                                x=df1['data'],
                                                y=df1[coluna_valor1],
                                                name=config_ind1['nome'],
                                                line=dict(color=config_ind1['cor'])
                                            ))
                                            
                                            # Adicionar segunda série com eixo Y secundário
                                            fig.add_trace(go.Scatter(
                                                x=df2['data'],
                                                y=df2[coluna_valor2],
                                                name=config_ind2['nome'],
                                                line=dict(color=config_ind2['cor']),
                                                yaxis="y2"
                                            ))
                                            
                                            # Configurar layout
                                            fig.update_layout(
                                                title=f"Comparação: {config_ind1['nome']} vs {config_ind2['nome']}",
                                                xaxis=dict(title="Data"),
                                                yaxis=dict(
                                                    title=f"{config_ind1['nome']} ({config_ind1['unidade']})",
                                                    titlefont=dict(color=config_ind1['cor']),
                                                    tickfont=dict(color=config_ind1['cor'])
                                                ),
                                                yaxis2=dict(
                                                    title=f"{config_ind2['nome']} ({config_ind2['unidade']})",
                                                    titlefont=dict(color=config_ind2['cor']),
                                                    tickfont=dict(color=config_ind2['cor']),
                                                    anchor="x",
                                                    overlaying="y",
                                                    side="right"
                                                ),
                                                legend=dict(
                                                    orientation="h",
                                                    yanchor="bottom",
                                                    y=1.02,
                                                    xanchor="right",
                                                    x=1
                                                )
                                            )
                                            
                                            # Exibir gráfico
                                            st.plotly_chart(fig, use_container_width=True)
                                            
                                            # Exibir correlação
                                            st.subheader("Análise de Correlação")
                                            
                                            # Mesclar os DataFrames pela data
                                            try:
                                                df_mesclado = pd.merge(df1, df2, on='data', suffixes=('_1', '_2'))
                                                
                                                if not df_mesclado.empty:
                                                    # Verificar se as colunas existem no DataFrame mesclado
                                                    coluna_valor1_mesclado = f"{coluna_valor1}_1"
                                                    coluna_valor2_mesclado = f"{coluna_valor2}_2"
                                                    
                                                    if coluna_valor1_mesclado in df_mesclado.columns and coluna_valor2_mesclado in df_mesclado.columns:
                                                        # Calcular correlação
                                                        correlacao = df_mesclado[coluna_valor1_mesclado].corr(df_mesclado[coluna_valor2_mesclado])
                                                        
                                                        # Exibir resultado
                                                        st.metric(
                                                            "Coeficiente de Correlação de Pearson", 
                                                            f"{correlacao:.4f}",
                                                            help="Varia de -1 (correlação negativa perfeita) a 1 (correlação positiva perfeita). Valores próximos de 0 indicam pouca ou nenhuma correlação."
                                                        )
                                                        
                                                        # Interpretar o resultado
                                                        if abs(correlacao) < 0.3:
                                                            interpretacao = "Correlação fraca"
                                                            cor_interpretacao = "orange"
                                                        elif abs(correlacao) < 0.7:
                                                            interpretacao = "Correlação moderada"
                                                            cor_interpretacao = "blue"
                                                        else:
                                                            interpretacao = "Correlação forte"
                                                            cor_interpretacao = "green"
                                                        
                                                        st.markdown(f"<p style='color:{cor_interpretacao};font-weight:bold;'>{interpretacao}</p>", unsafe_allow_html=True)
                                                        
                                                        # Exibir gráfico de dispersão
                                                        try:
                                                            fig_scatter = px.scatter(
                                                                df_mesclado, 
                                                                x=coluna_valor1_mesclado, 
                                                                y=coluna_valor2_mesclado,
                                                                trendline="ols",
                                                                labels={
                                                                    coluna_valor1_mesclado: f"{config_ind1['nome']} ({config_ind1['unidade']})",
                                                                    coluna_valor2_mesclado: f"{config_ind2['nome']} ({config_ind2['unidade']})"
                                                                },
                                                                title=f"Dispersão: {config_ind1['nome']} vs {config_ind2['nome']}"
                                                            )
                                                            
                                                            # Exibir gráfico
                                                            st.plotly_chart(fig_scatter, use_container_width=True)
                                                        except Exception as e:
                                                            logger.error(f"Erro ao criar gráfico de dispersão: {str(e)}")
                                                            st.warning("Não foi possível criar o gráfico de dispersão.")
                                                    else:
                                                        st.warning("Colunas de valor não encontradas após mesclar os dados.")
                                                else:
                                                    st.warning("Não há dados com datas coincidentes para os indicadores selecionados.")
                                            except Exception as e:
                                                logger.error(f"Erro ao mesclar DataFrames: {str(e)}")
                                                st.warning("Erro ao analisar correlação entre os indicadores.")
                                        except Exception as e:
                                            logger.error(f"Erro ao exibir comparação: {str(e)}")
                                            st.warning("Erro ao exibir comparação entre indicadores")
            except Exception as e:
                logger.error(f"Erro na aba Comparativo: {str(e)}")
                st.error(f"Ocorreu um erro na aba Comparativo: {str(e)}")
        
        # Aba de Previsões
        with tab_previsoes:
            try:
                st.header("Projeções Futuras")
                
                if not mostrar_projecoes:
                    st.info("Ative a opção 'Mostrar projeções futuras' no painel lateral para visualizar as projeções.")
                else:
                    # Seleção do indicador para projeção
                    try:
                        id_indicador_prev = st.selectbox(
                            "Selecione o indicador para projeção:",
                            options=indicadores_selecionados if indicadores_selecionados else list(config_indicadores.keys()),
                            format_func=lambda x: config_indicadores[x]['nome'],
                            key="prev_ind"
                        )
                    except Exception as e:
                        logger.error(f"Erro ao criar seletor de indicador para projeção: {str(e)}")
                        # Fallback para primeiro indicador
                        id_indicador_prev = indicadores_selecionados[0] if indicadores_selecionados else list(config_indicadores.keys())[0]
                        st.warning("Erro ao criar seletor de indicador para projeção. Usando primeiro indicador.")
                    
                    # Usar a função robusta para exibir projeções
                    exibir_projecoes_robusta(id_indicador_prev, projecoes_indicadores, dados_filtrados, config_indicadores)
            except Exception as e:
                logger.error(f"Erro na aba Previsões: {str(e)}")
                st.error(f"Ocorreu um erro na aba Previsões: {str(e)}")
        
        # Aba de Exportação
        with tab_exportar:
            try:
                st.header("Exportar Dados")
                
                # Seleção do indicador para exportação
                try:
                    id_indicador_exp = st.selectbox(
                        "Selecione o indicador para exportação:",
                        options=indicadores_selecionados if indicadores_selecionados else list(config_indicadores.keys()),
                        format_func=lambda x: config_indicadores[x]['nome'],
                        key="exp_ind"
                    )
                except Exception as e:
                    logger.error(f"Erro ao criar seletor de indicador para exportação: {str(e)}")
                    # Fallback para primeiro indicador
                    id_indicador_exp = indicadores_selecionados[0] if indicadores_selecionados else list(config_indicadores.keys())[0]
                    st.warning("Erro ao criar seletor de indicador para exportação. Usando primeiro indicador.")
                
                # Verificar se o indicador existe na configuração
                if id_indicador_exp not in config_indicadores:
                    st.warning(f"Configuração não encontrada para o indicador {id_indicador_exp}")
                else:
                    # Obter configuração do indicador
                    config_ind = config_indicadores[id_indicador_exp]
                    
                    # Verificar se há dados para o indicador selecionado
                    if id_indicador_exp not in dados_filtrados or dados_filtrados[id_indicador_exp].empty:
                        st.info(f"Não há dados disponíveis para {config_ind['nome']} no período selecionado.")
                    else:
                        # Exibir opções de exportação
                        st.subheader("Opções de Exportação")
                        
                        # Seleção do formato
                        try:
                            formato_exp = st.radio(
                                "Selecione o formato de exportação:",
                                options=["CSV", "Excel", "JSON"],
                                horizontal=True
                            )
                        except Exception as e:
                            logger.error(f"Erro ao criar seletor de formato de exportação: {str(e)}")
                            formato_exp = "CSV"
                            st.warning("Erro ao criar seletor de formato. Usando CSV como padrão.")
                        
                        # Opção para incluir projeções
                        try:
                            incluir_projecoes = st.checkbox(
                                "Incluir projeções",
                                value=True if mostrar_projecoes and id_indicador_exp in projecoes_indicadores and not projecoes_indicadores[id_indicador_exp].empty else False,
                                disabled=not (mostrar_projecoes and id_indicador_exp in projecoes_indicadores and not projecoes_indicadores[id_indicador_exp].empty)
                            )
                        except Exception as e:
                            logger.error(f"Erro ao criar checkbox de inclusão de projeções: {str(e)}")
                            incluir_projecoes = False
                            st.warning("Erro ao criar opção de inclusão de projeções. Projeções não serão incluídas.")
                        
                        # Botão de exportação
                        if st.button("Exportar Dados"):
                            try:
                                # Obter DataFrame
                                df_exp = dados_filtrados[id_indicador_exp].copy()
                                
                                # Incluir projeções se solicitado
                                if incluir_projecoes and id_indicador_exp in projecoes_indicadores and not projecoes_indicadores[id_indicador_exp].empty:
                                    try:
                                        df_proj = projecoes_indicadores[id_indicador_exp].copy()
                                        
                                        # Verificar e mapear colunas do DataFrame de projeção
                                        colunas_data = ['ds', 'data']  # Possíveis nomes para coluna de data
                                        colunas_valor = ['yhat', 'valor', 'projecao']  # Possíveis nomes para coluna de valor
                                        colunas_limite_inf = ['yhat_lower', 'limite_inferior']  # Possíveis nomes para limite inferior
                                        colunas_limite_sup = ['yhat_upper', 'limite_superior']  # Possíveis nomes para limite superior
                                        
                                        # Encontrar coluna de data
                                        coluna_data_proj = None
                                        for col in colunas_data:
                                            if col in df_proj.columns:
                                                coluna_data_proj = col
                                                break
                                        
                                        # Encontrar coluna de valor
                                        coluna_valor_proj = None
                                        for col in colunas_valor:
                                            if col in df_proj.columns:
                                                coluna_valor_proj = col
                                                break
                                        
                                        if coluna_data_proj and coluna_valor_proj:
                                            # Renomear colunas para padronização
                                            mapeamento_colunas = {coluna_data_proj: 'data', coluna_valor_proj: 'projecao'}
                                            
                                            # Adicionar mapeamento para limites se existirem
                                            for col in colunas_limite_inf:
                                                if col in df_proj.columns:
                                                    mapeamento_colunas[col] = 'limite_inferior'
                                                    break
                                            
                                            for col in colunas_limite_sup:
                                                if col in df_proj.columns:
                                                    mapeamento_colunas[col] = 'limite_superior'
                                                    break
                                            
                                            # Renomear colunas
                                            df_proj = df_proj.rename(columns=mapeamento_colunas)
                                            
                                            # Adicionar coluna de tipo
                                            df_exp['tipo'] = 'historico'
                                            df_proj['tipo'] = 'projecao'
                                            
                                            # Selecionar colunas relevantes
                                            coluna_valor = obter_coluna_valor(df_exp)
                                            if coluna_valor:
                                                # Adicionar colunas de valor às projeções
                                                if coluna_valor not in df_proj.columns:
                                                    df_proj[coluna_valor] = None
                                                
                                                # Concatenar DataFrames
                                                df_exp = pd.concat([df_exp, df_proj], ignore_index=True)
                                        else:
                                            st.warning("Não foi possível incluir projeções devido a incompatibilidade de formato")
                                    except Exception as e:
                                        logger.error(f"Erro ao incluir projeções na exportação: {str(e)}")
                                        st.warning(f"Não foi possível incluir projeções: {str(e)}")
                                
                                # Exportar conforme formato selecionado
                                nome_arquivo = f"{id_indicador_exp}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                
                                if formato_exp == "CSV":
                                    # Exportar para CSV
                                    try:
                                        caminho_arquivo = exportador.exportar_csv(df_exp, nome_arquivo)
                                        st.success(f"Dados exportados com sucesso para {caminho_arquivo}")
                                        
                                        # Oferecer download
                                        with open(caminho_arquivo, 'r') as f:
                                            st.download_button(
                                                label="Baixar arquivo CSV",
                                                data=f,
                                                file_name=f"{nome_arquivo}.csv",
                                                mime="text/csv"
                                            )
                                    except Exception as e:
                                        logger.error(f"Erro ao exportar para CSV: {str(e)}")
                                        st.error(f"Erro ao exportar para CSV: {str(e)}")
                                
                                elif formato_exp == "Excel":
                                    # Exportar para Excel
                                    try:
                                        caminho_arquivo = exportador.exportar_excel(df_exp, nome_arquivo)
                                        st.success(f"Dados exportados com sucesso para {caminho_arquivo}")
                                        
                                        # Oferecer download
                                        with open(caminho_arquivo, 'rb') as f:
                                            st.download_button(
                                                label="Baixar arquivo Excel",
                                                data=f,
                                                file_name=f"{nome_arquivo}.xlsx",
                                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                            )
                                    except Exception as e:
                                        logger.error(f"Erro ao exportar para Excel: {str(e)}")
                                        st.error(f"Erro ao exportar para Excel: {str(e)}")
                                
                                elif formato_exp == "JSON":
                                    # Exportar para JSON
                                    try:
                                        caminho_arquivo = exportador.exportar_json(df_exp, nome_arquivo)
                                        st.success(f"Dados exportados com sucesso para {caminho_arquivo}")
                                        
                                        # Oferecer download
                                        with open(caminho_arquivo, 'r') as f:
                                            st.download_button(
                                                label="Baixar arquivo JSON",
                                                data=f,
                                                file_name=f"{nome_arquivo}.json",
                                                mime="application/json"
                                            )
                                    except Exception as e:
                                        logger.error(f"Erro ao exportar para JSON: {str(e)}")
                                        st.error(f"Erro ao exportar para JSON: {str(e)}")
                            
                            except Exception as e:
                                logger.error(f"Erro ao exportar dados: {str(e)}")
                                st.error(f"Erro ao exportar dados: {str(e)}")
            except Exception as e:
                logger.error(f"Erro na aba Exportar: {str(e)}")
                st.error(f"Ocorreu um erro na aba Exportar: {str(e)}")
    except Exception as e:
        logger.error(f"Erro geral no dashboard: {str(e)}")
        st.error(f"Ocorreu um erro no dashboard: {str(e)}")

    st.mardown("---")
    st.caption("Desenvolvido por Márcio Lemos")
# Executar o dashboard
if __name__ == "__main__":
    main()
