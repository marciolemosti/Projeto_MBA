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

# CONFIGURAÇÃO DA PÁGINA STREAMLIT
st.set_page_config(
    page_title="Dashboard de Indicadores Socioeconômicos Brasileiros",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Detectar e configurar caminhos automaticamente
def setup_paths():
    """Configura os caminhos de importação automaticamente"""
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    
    # Procurar pelo diretório raiz do projeto (que contém 'src')
    projeto_root = current_dir
    while projeto_root != os.path.dirname(projeto_root):  # Não chegou na raiz do sistema
        if os.path.exists(os.path.join(projeto_root, 'src')):
            break
        projeto_root = os.path.dirname(projeto_root)
    
    # Se não encontrou, assumir que está em src/visualizacao
    if not os.path.exists(os.path.join(projeto_root, 'src')):
        projeto_root = os.path.dirname(os.path.dirname(current_dir))
    
    src_path = os.path.join(projeto_root, 'src')
    
    # Adicionar caminhos ao PYTHONPATH
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    if projeto_root not in sys.path:
        sys.path.insert(0, projeto_root)
    
    return projeto_root, src_path

# Configurar caminhos
try:
    PROJETO_ROOT, SRC_PATH = setup_paths()
    # Remover st.success() daqui para evitar conflito com set_page_config
    print(f"✅ Caminhos configurados: {PROJETO_ROOT}")  # Log no console em vez de Streamlit
except Exception as e:
    print(f"❌ Erro ao configurar caminhos: {e}")
    PROJETO_ROOT = os.getcwd()
    SRC_PATH = os.path.join(PROJETO_ROOT, 'src')

# Importar utilitários
try:
    from utils.cache import cache_manager, dataframe_cache
    from utils.config import config_manager
    print("✅ Utilitários importados com sucesso")
except ImportError as e:
    print(f"⚠️ Erro ao importar utilitários: {e}")
    # Criar mocks simples
    class MockCache:
        def get(self, key): return None
        def set(self, key, value, ttl=None): pass
        def clear(self): pass
    
    class MockConfig:
        def get(self, key, default=None): return default
        def obter_config_indicador(self, ind): return {'nome': ind, 'cor': '#666', 'unidade': ''}
    
    cache_manager = MockCache()
    dataframe_cache = MockCache()
    config_manager = MockConfig()

# Importar módulos de dados
try:
    from dados.extratores.bcb import ExtratorBCB
    from dados.extratores.ibge import ExtratorIBGE
    from dados.processadores.previsao import PrevisorSeriesTemporal
    print("✅ Módulos de dados importados com sucesso")
except ImportError as e:
    print(f"⚠️ Erro ao importar módulos de dados: {e}")
    # Criar classes mock para demonstração
    class MockExtrator:
        def __init__(self, *args, **kwargs): pass
        def obter_dados(self, *args, **kwargs): return pd.DataFrame()
    
    class MockPrevisor:
        def __init__(self, *args, **kwargs): pass
        def gerar_previsao(self, *args, **kwargs): return pd.DataFrame(), {}
    
    ExtratorBCB = MockExtrator
    ExtratorIBGE = MockExtrator
    PrevisorSeriesTemporal = MockPrevisor
    
    # Agora podemos usar st.warning() pois set_page_config já foi executado
    st.warning("⚠️ Executando em modo de demonstração com dados mock")

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes
DIRETORIO_DADOS = os.path.join(PROJETO_ROOT, "data")

def verificar_ambiente():
    """Verifica se o ambiente está configurado corretamente"""
    problemas = []
    
    # Verificar diretório de dados
    if not os.path.exists(DIRETORIO_DADOS):
        problemas.append(f"Diretório de dados não encontrado: {DIRETORIO_DADOS}")
    
    # Verificar arquivos de dados essenciais
    arquivos_essenciais = ['ipca.json', 'selic.json', 'cambio_ptax_venda.json']
    for arquivo in arquivos_essenciais:
        caminho = os.path.join(DIRETORIO_DADOS, arquivo)
        if not os.path.exists(caminho):
            problemas.append(f"Arquivo de dados não encontrado: {arquivo}")
    
    return problemas

@st.cache_data(ttl=1800)  # Cache por 30 minutos
def carregar_dados() -> Dict[str, pd.DataFrame]:
    """
    Carrega todos os dados dos indicadores econômicos
    
    Returns:
        Dicionário com DataFrames dos indicadores
    """
    logger.info("Carregando dados dos indicadores...")
    
    # Verificar cache primeiro
    dados_cache = cache_manager.get('dados_indicadores')
    if dados_cache is not None:
        logger.info("Dados carregados do cache")
        return dados_cache
    
    # Inicializar dicionário com DataFrames vazios
    dados_indicadores = {
        'ipca': pd.DataFrame(),
        'selic': pd.DataFrame(),
        'cambio': pd.DataFrame(),
        'deficit_primario': pd.DataFrame(),
        'iof': pd.DataFrame(),
        'pib': pd.DataFrame(),
        'desemprego': pd.DataFrame()
    }
    
    try:
        # Mapeamento de indicadores para arquivos
        arquivos_dados = {
            'ipca': 'ipca.json',
            'selic': 'selic.json',
            'cambio': 'cambio_ptax_venda.json',
            'deficit_primario': 'deficit_primario.json',
            'iof': 'arrecadacao_iof.json',
            'pib': 'pib.json',
            'desemprego': 'desemprego.json'
        }
        
        # Carregar cada arquivo
        for id_indicador, nome_arquivo in arquivos_dados.items():
            caminho_arquivo = os.path.join(DIRETORIO_DADOS, nome_arquivo)
            
            if os.path.exists(caminho_arquivo):
                try:
                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        dados_json = json.load(f)
                    
                    if dados_json:
                        df = pd.DataFrame(dados_json)
                        if 'data' in df.columns:
                            df['data'] = pd.to_datetime(df['data'])
                            df = df.sort_values('data')
                        dados_indicadores[id_indicador] = df
                        logger.info(f"Carregado {id_indicador}: {len(df)} registros")
                    
                except Exception as e:
                    logger.error(f"Erro ao carregar {nome_arquivo}: {e}")
                    dados_indicadores[id_indicador] = pd.DataFrame()
            else:
                logger.warning(f"Arquivo não encontrado: {nome_arquivo}")
        
        # Salvar no cache
        cache_manager.set('dados_indicadores', dados_indicadores, ttl=1800)
        logger.info("Dados salvos no cache")
        
    except Exception as e:
        logger.error(f"Erro geral ao carregar dados: {e}")
        # Em caso de erro, retornar DataFrames vazios
        pass
    
    return dados_indicadores

@st.cache_data(ttl=1800)
def atualizar_dados_bcb():
    """Atualiza dados do BCB via API"""
    try:
        logger.info("Atualizando dados do BCB...")
        
        # Verificar cache
        dados_cache = cache_manager.get('dados_bcb_atualizados')
        if dados_cache is not None:
            return dados_cache
        
        # Inicializar dicionário com DataFrames vazios
        dados_indicadores = {
            'ipca': pd.DataFrame(),
            'selic': pd.DataFrame(),
            'cambio': pd.DataFrame(),
            'deficit_primario': pd.DataFrame(),
            'iof': pd.DataFrame(),
            'pib': pd.DataFrame(),
            'desemprego': pd.DataFrame()
        }
        
        try:
            # Criar extrator BCB
            extrator_bcb = ExtratorBCB(diretorio_dados=DIRETORIO_DADOS)
            
            logger.info("Dados do BCB atualizados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao atualizar dados do BCB: {e}")
        
        # Salvar no cache
        cache_manager.set('dados_bcb_atualizados', dados_indicadores, ttl=1800)
        
        return dados_indicadores
        
    except Exception as e:
        logger.error(f"Erro ao atualizar dados do BCB: {e}")
        return carregar_dados()

def obter_coluna_valor(df: pd.DataFrame, indicador: str) -> str:
    """
    Determina qual coluna usar para o valor do indicador
    
    Args:
        df: DataFrame do indicador
        indicador: ID do indicador
        
    Returns:
        Nome da coluna de valor
    """
    if df.empty:
        return 'valor'
    
    # Mapeamento de colunas preferenciais por indicador
    colunas_preferenciais = {
        'ipca': ['valor', 'variacao_mensal', 'indice'],
        'selic': ['valor', 'taxa', 'meta_selic'],
        'cambio': ['valor', 'cotacao_compra', 'cotacao_venda'],
        'deficit_primario': ['valor', 'resultado_primario'],
        'iof': ['valor', 'arrecadacao'],
        'pib': ['valor', 'variacao_trimestral', 'pib_variacao'],
        'desemprego': ['valor', 'taxa_desocupacao', 'desemprego']
    }
    
    colunas_disponiveis = df.columns.tolist()
    colunas_candidatas = colunas_preferenciais.get(indicador, ['valor'])
    
    # Procurar primeira coluna disponível
    for coluna in colunas_candidatas:
        if coluna in colunas_disponiveis:
            return coluna
    
    # Se não encontrou, usar primeira coluna numérica
    for coluna in colunas_disponiveis:
        if coluna != 'data' and df[coluna].dtype in ['int64', 'float64']:
            return coluna
    
    # Fallback
    return 'valor' if 'valor' in colunas_disponiveis else colunas_disponiveis[0]

def criar_grafico_linha(df: pd.DataFrame, indicador: str, config: Dict[str, Any]) -> go.Figure:
    """
    Cria gráfico de linha para um indicador
    
    Args:
        df: DataFrame com os dados
        indicador: ID do indicador
        config: Configuração do indicador
        
    Returns:
        Figura do Plotly
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Dados não disponíveis",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    coluna_valor = obter_coluna_valor(df, indicador)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['data'],
        y=df[coluna_valor],
        mode='lines+markers',
        name=config.get('nome', indicador),
        line=dict(color=config.get('cor', '#1f77b4'), width=2),
        marker=dict(size=4),
        hovertemplate=f"<b>{config.get('nome', indicador)}</b><br>" +
                     "Data: %{x}<br>" +
                     f"Valor: %{{y:.2f}} {config.get('unidade', '')}<br>" +
                     "<extra></extra>"
    ))
    
    fig.update_layout(
        title=f"{config.get('nome', indicador)} - Série Histórica",
        xaxis_title="Data",
        yaxis_title=f"{config.get('nome', indicador)} ({config.get('unidade', '')})",
        hovermode='x unified',
        showlegend=False,
        height=400
    )
    
    return fig

def criar_grafico_comparacao(dados: Dict[str, pd.DataFrame], indicadores_selecionados: List[str]) -> go.Figure:
    """
    Cria gráfico de comparação entre múltiplos indicadores
    
    Args:
        dados: Dicionário com DataFrames dos indicadores
        indicadores_selecionados: Lista de indicadores para comparar
        
    Returns:
        Figura do Plotly
    """
    fig = go.Figure()
    
    for indicador in indicadores_selecionados:
        if indicador in dados and not dados[indicador].empty:
            df = dados[indicador]
            config = config_manager.obter_config_indicador(indicador)
            coluna_valor = obter_coluna_valor(df, indicador)
            
            fig.add_trace(go.Scatter(
                x=df['data'],
                y=df[coluna_valor],
                mode='lines',
                name=config.get('nome', indicador),
                line=dict(color=config.get('cor', '#1f77b4'), width=2),
                hovertemplate=f"<b>{config.get('nome', indicador)}</b><br>" +
                             "Data: %{x}<br>" +
                             f"Valor: %{{y:.2f}} {config.get('unidade', '')}<br>" +
                             "<extra></extra>"
            ))
    
    fig.update_layout(
        title="Comparação de Indicadores",
        xaxis_title="Data",
        yaxis_title="Valor",
        hovermode='x unified',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def gerar_previsao_indicador(df: pd.DataFrame, indicador: str, periodos: int = 24) -> Tuple[pd.DataFrame, Dict]:
    """
    Gera previsão para um indicador usando Prophet
    
    Args:
        df: DataFrame com dados históricos
        indicador: ID do indicador
        periodos: Número de períodos para prever
        
    Returns:
        Tupla com DataFrame de previsão e métricas
    """
    if df.empty or len(df) < 10:
        return pd.DataFrame(), {}
    
    try:
        previsor = PrevisorSeriesTemporal()
        df_previsao, metricas = previsor.gerar_previsao(
            dados=df,
            coluna_data='data',
            coluna_valor=obter_coluna_valor(df, indicador),
            periodos_futuros=periodos
        )
        
        return df_previsao, metricas
        
    except Exception as e:
        logger.error(f"Erro ao gerar previsão para {indicador}: {e}")
        return pd.DataFrame(), {}

def criar_grafico_previsao(df_historico: pd.DataFrame, df_previsao: pd.DataFrame, 
                          indicador: str, config: Dict[str, Any]) -> go.Figure:
    """
    Cria gráfico com dados históricos e previsão
    
    Args:
        df_historico: DataFrame com dados históricos
        df_previsao: DataFrame com previsão
        indicador: ID do indicador
        config: Configuração do indicador
        
    Returns:
        Figura do Plotly
    """
    fig = go.Figure()
    
    if not df_historico.empty:
        coluna_valor = obter_coluna_valor(df_historico, indicador)
        
        # Dados históricos
        fig.add_trace(go.Scatter(
            x=df_historico['data'],
            y=df_historico[coluna_valor],
            mode='lines+markers',
            name='Histórico',
            line=dict(color=config.get('cor', '#1f77b4'), width=2),
            marker=dict(size=4)
        ))
    
    if not df_previsao.empty and 'ds' in df_previsao.columns:
        # Previsão
        fig.add_trace(go.Scatter(
            x=df_previsao['ds'],
            y=df_previsao['yhat'],
            mode='lines',
            name='Previsão',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        # Intervalo de confiança
        if 'yhat_lower' in df_previsao.columns and 'yhat_upper' in df_previsao.columns:
            fig.add_trace(go.Scatter(
                x=df_previsao['ds'],
                y=df_previsao['yhat_upper'],
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig.add_trace(go.Scatter(
                x=df_previsao['ds'],
                y=df_previsao['yhat_lower'],
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.2)',
                name='Intervalo de Confiança',
                hoverinfo='skip'
            ))
    
    fig.update_layout(
        title=f"{config.get('nome', indicador)} - Projeção de IPCA para os próximos 2 anos",
        xaxis_title="Data",
        yaxis_title=f"{config.get('nome', indicador)} ({config.get('unidade', '')})",
        hovermode='x unified',
        height=500
    )
    
    return fig

def exibir_metricas_indicador(df: pd.DataFrame, indicador: str, config: Dict[str, Any]):
    """
    Exibe métricas resumidas de um indicador
    
    Args:
        df: DataFrame do indicador
        indicador: ID do indicador
        config: Configuração do indicador
    """
    if df.empty:
        st.warning(f"Dados não disponíveis para {config.get('nome', indicador)}")
        return
    
    coluna_valor = obter_coluna_valor(df, indicador)
    
    # Calcular métricas
    valor_atual = df[coluna_valor].iloc[-1] if len(df) > 0 else 0
    valor_anterior = df[coluna_valor].iloc[-2] if len(df) > 1 else valor_atual
    variacao = valor_atual - valor_anterior
    variacao_pct = (variacao / valor_anterior * 100) if valor_anterior != 0 else 0
    
    media = df[coluna_valor].mean()
    maximo = df[coluna_valor].max()
    minimo = df[coluna_valor].min()
    
    # Exibir métricas em colunas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Valor Atual",
            value=f"{valor_atual:.2f} {config.get('unidade', '')}",
            delta=f"{variacao:+.2f} ({variacao_pct:+.1f}%)"
        )
    
    with col2:
        st.metric(
            label="Média Histórica",
            value=f"{media:.2f} {config.get('unidade', '')}"
        )
    
    with col3:
        st.metric(
            label="Máximo",
            value=f"{maximo:.2f} {config.get('unidade', '')}"
        )
    
    with col4:
        st.metric(
            label="Mínimo",
            value=f"{minimo:.2f} {config.get('unidade', '')}"
        )

def main():
    """Função principal do dashboard"""
    try:
        # Verificar ambiente
        problemas = verificar_ambiente()
        if problemas:
            st.error("⚠️ Problemas detectados no ambiente:")
            for problema in problemas:
                st.error(f"• {problema}")
            st.info("💡 Executando com dados de demonstração")
        
        # Título principal
        st.title("📊 Termômetro da Economia Brasileira")
        st.markdown("### Dashboard Interativo de Indicadores Econômicos")
        
        # Sidebar para controles
        with st.sidebar:
            st.header("🎛️ Controles")
            
            # Atualização de dados
            if st.button("🔄 Atualizar Dados"):
                cache_manager.clear()
                st.rerun()
            
            # Seleção de indicadores
            st.subheader("📈 Indicadores")
            
            # Configuração dos indicadores
            config_indicadores = {
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
            }
            
            opcoes_indicadores = list(config_indicadores.keys())
            nomes_indicadores = [config_indicadores[ind]['nome'] for ind in opcoes_indicadores]
            
            indicadores_selecionados = st.multiselect(
                "Selecione os indicadores:",
                options=opcoes_indicadores,
                format_func=lambda x: config_indicadores[x]['nome'],
                default=['deficit_primario', 'iof', 'ipca'],
                help="Escolha quais indicadores visualizar"
            )
            
            if not indicadores_selecionados:
                indicadores_selecionados = ['deficit_primario', 'iof', 'ipca']
            
            # Período de análise
            st.subheader("📅 Período")
            periodo_meses = st.slider(
                "Últimos meses:",
                min_value=6,
                max_value=60,
                value=24,
                help="Período para análise dos dados"
            )
        
        # Carregar dados
        with st.spinner("Carregando dados..."):
            try:
                dados_indicadores = carregar_dados()
            except Exception as e:
                logger.error(f"Erro ao carregar dados: {e}")
                st.error(f"Erro ao carregar dados: {e}")
                try:
                    dados_indicadores = atualizar_dados_bcb()
                except Exception as e2:
                    logger.error(f"Erro ao atualizar dados do BCB: {e2}")
                    # Fallback para dados vazios
                    dados_indicadores = {
                        'ipca': pd.DataFrame(),
                        'selic': pd.DataFrame(),
                        'cambio': pd.DataFrame(),
                        'deficit_primario': pd.DataFrame(),
                        'iof': pd.DataFrame(),
                        'pib': pd.DataFrame(),
                        'desemprego': pd.DataFrame()
                    }
        
        # Abas principais
        tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "📈 Análise Individual", "🔮 Projeções"])
        
        with tab1:
            st.header("📊 Visão Geral dos Indicadores")
            
            # Gráfico de comparação
            if indicadores_selecionados:
                fig_comparacao = criar_grafico_comparacao(dados_indicadores, indicadores_selecionados)
                st.plotly_chart(fig_comparacao, use_container_width=True)
            
            # Métricas resumidas
            st.subheader("📋 Resumo dos Indicadores")
            
            cols = st.columns(min(len(indicadores_selecionados), 3))
            for i, indicador in enumerate(indicadores_selecionados):
                with cols[i % 3]:
                    config = config_indicadores.get(indicador, {})
                    df = dados_indicadores.get(indicador, pd.DataFrame())
                    
                    if not df.empty:
                        coluna_valor = obter_coluna_valor(df, indicador)
                        valor_atual = df[coluna_valor].iloc[-1]
                        
                        st.metric(
                            label=config.get('nome', indicador),
                            value=f"{valor_atual:.2f} {config.get('unidade', '')}",
                            help=config.get('descricao', '')
                        )
                    else:
                        st.metric(
                            label=config.get('nome', indicador),
                            value="N/A",
                            help="Dados não disponíveis"
                        )
        
        with tab2:
            st.header("📈 Análise Individual dos Indicadores")
            
            # Seletor de indicador para análise detalhada
            indicador_analise = st.selectbox(
                "Selecione um indicador para análise detalhada:",
                options=indicadores_selecionados,
                format_func=lambda x: config_indicadores[x]['nome'],
                help="Escolha um indicador para análise aprofundada"
            )
            
            if indicador_analise:
                config = config_indicadores[indicador_analise]
                df = dados_indicadores.get(indicador_analise, pd.DataFrame())
                
                st.subheader(f"📊 {config['nome']}")
                st.markdown(f"**Descrição:** {config['descricao']}")
                
                if not df.empty:
                    # Filtrar por período
                    data_limite = datetime.now() - timedelta(days=periodo_meses * 30)
                    df_filtrado = df[df['data'] >= data_limite] if 'data' in df.columns else df
                    
                    # Métricas
                    exibir_metricas_indicador(df_filtrado, indicador_analise, config)
                    
                    # Gráfico
                    fig = criar_grafico_linha(df_filtrado, indicador_analise, config)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabela de dados
                    with st.expander("📋 Dados Detalhados"):
                        st.dataframe(df_filtrado.tail(20), use_container_width=True)
                else:
                    st.warning(f"Dados não disponíveis para {config['nome']}")
        
        with tab3:
            st.header("🔮 Projeções dos Indicadores")
            
            # Seletor de indicador para projeção
            indicador_projecao = st.selectbox(
                "Selecione um indicador para projeção:",
                options=indicadores_selecionados,
                format_func=lambda x: config_indicadores[x]['nome'],
                help="Escolha um indicador para gerar projeções"
            )
            
            if indicador_projecao:
                config = config_indicadores[indicador_projecao]
                df = dados_indicadores.get(indicador_projecao, pd.DataFrame())
                
                st.subheader(f"🔮 Projeção: {config['nome']}")
                
                if not df.empty and len(df) >= 10:
                    # Parâmetros da projeção
                    col1, col2 = st.columns(2)
                    with col1:
                        periodos_projecao = st.slider(
                            "Períodos para projetar:",
                            min_value=6,
                            max_value=36,
                            value=24,
                            help="Número de períodos futuros para projetar"
                        )
                    
                    with col2:
                        if st.button("🚀 Gerar Projeção"):
                            with st.spinner("Gerando projeção..."):
                                df_previsao, metricas = gerar_previsao_indicador(
                                    df, indicador_projecao, periodos_projecao
                                )
                                
                                if not df_previsao.empty:
                                    # Gráfico de projeção
                                    fig_previsao = criar_grafico_previsao(
                                        df, df_previsao, indicador_projecao, config
                                    )
                                    st.plotly_chart(fig_previsao, use_container_width=True)
                                    
                                    # Métricas da projeção
                                    if metricas:
                                        st.subheader("📊 Métricas da Projeção")
                                        col1, col2, col3 = st.columns(3)
                                        
                                        with col1:
                                            if 'mae' in metricas:
                                                st.metric("MAE", f"{metricas['mae']:.4f}")
                                        
                                        with col2:
                                            if 'mape' in metricas:
                                                st.metric("MAPE", f"{metricas['mape']:.2f}%")
                                        
                                        with col3:
                                            if 'rmse' in metricas:
                                                st.metric("RMSE", f"{metricas['rmse']:.4f}")
                                    
                                    # Tabela de projeções
                                    with st.expander("📋 Dados da Projeção"):
                                        st.dataframe(df_previsao.head(20), use_container_width=True)
                                else:
                                    st.error("Não foi possível gerar a projeção. Verifique os dados.")
                else:
                    st.warning(f"Dados insuficientes para projeção de {config['nome']} (mínimo: 10 registros)")
        
        # Rodapé com informações
        st.markdown("---")
        
        # Seção de créditos e fontes
        col1, col2 = st.columns([2, 1])
        
        with col1:
            with st.expander("📊 Fontes dos Dados"):
                st.markdown("""
                **Dados Reais:**
                - **IPCA**: IBGE (Instituto Brasileiro de Geografia e Estatística)
                - **Taxa Selic**: BCB (Banco Central do Brasil)
                - **Câmbio USD/BRL**: BCB (Banco Central do Brasil)
                - **Déficit Primário**: Tesouro Nacional / BCB
                - **Arrecadação IOF**: Receita Federal / BCB
                
                **Dados de Amostragem:**
                - **PIB**: Dados simulados baseados em padrões históricos
                - **Taxa de Desemprego**: Dados simulados baseados em padrões históricos
                
                **Metodologia:**
                - **Projeções**: Facebook Prophet com sazonalidade automática
                - **Cache**: Sistema otimizado para performance
                - **Atualização**: Dados atualizados periodicamente via APIs oficiais
                
                **Limitações:**
                - Projeções são estimativas baseadas em dados históricos
                - Dados de amostra são apenas para demonstração
                - Resultados não constituem recomendação de investimento
                """)
        
        with col2:
            st.markdown("""
            <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px;'>
                <h4>📊 Dashboard Econômico</h4>
                <p><strong>Desenvolvido por:</strong><br>Márcio Lemos</p>
                <p><small>Termômetro da Economia Brasileira<br>Versão 2.0</small></p>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        logger.error(f"Erro na função principal: {e}")
        st.error(f"Erro inesperado: {e}")
        st.info("Tente recarregar a página ou verificar os logs para mais detalhes.")

if __name__ == "__main__":
    main()


