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
from src.dados.extratores.bcb import ExtratorBCB
from src.dados.extratores.ibge import ExtratorIBGE
from src.dados.processadores.previsao import PrevisorSeriesTemporal, gerar_previsoes_para_indicadores
from src.dados.processadores.eventos import DetectorEventos
from src.visualizacao.componentes.exibidores import ExibidorMetricas, ExibidorGraficos
from src.visualizacao.componentes.exportadores import Exportador
from src.utils.configuracao import obter_configuracao

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
config = obter_configuracao()

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
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Criar diretório de dados se não existir
    os.makedirs(DIRETORIO_DADOS, exist_ok=True)
    
    # Salvar em arquivo JSON
    with open(ARQUIVO_ULTIMA_ATUALIZACAO, 'w', encoding='utf-8') as f:
        json.dump({"ultima_atualizacao": data_atual}, f)
    
    return data_atual

# Função para carregar a data da última atualização
def carregar_data_atualizacao():
    """
    Carrega a data e hora da última atualização dos dados.
    
    Returns:
        String com a data e hora ou "Nunca atualizado" se não houver registro
    """
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
                    df['data'] = pd.to_datetime(df['data'])
                
                # Adicionar ao dicionário
                dados[id_indicador] = df
                
                logger.info(f"Dados carregados para {id_indicador}: {len(df)} registros")
                
            except Exception as e:
                logger.error(f"Erro ao carregar dados de {id_indicador}: {str(e)}")
                # Manter DataFrame vazio para este indicador
        else:
            logger.warning(f"Arquivo não encontrado para {id_indicador}: {caminho_arquivo}")
            # DataFrame vazio já inicializado
    
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
                            df['data'] = pd.to_datetime(df['data'])
                        
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
    
    return eventos

# Função principal
def main():
    """Função principal do dashboard."""
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
                dados_indicadores = atualizar_dados()
                st.session_state['dados_indicadores'] = dados_indicadores
                st.session_state['dados_atualizados'] = True
                st.success("Dados atualizados com sucesso!")
        
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
                    anos = df['data'].dt.year.unique().tolist()
                    anos_disponiveis.extend(anos)
        
        anos_disponiveis = sorted(list(set(anos_disponiveis)))
        
        if not anos_disponiveis:
            anos_disponiveis = list(range(2010, datetime.now().year + 1))
        
        # Slider para seleção de anos
        ano_min, ano_max = st.select_slider(
            "Selecione o intervalo de anos:",
            options=anos_disponiveis,
            value=(min(anos_disponiveis), max(anos_disponiveis))
        )
        
        anos_selecionados = list(range(ano_min, ano_max + 1))
        
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
        indicadores_selecionados = st.multiselect(
            "Selecione os indicadores:",
            options=list(config_indicadores.keys()),
            default=['pib', 'desemprego', 'deficit_primario', 'iof'],
            format_func=lambda x: config_indicadores[x]['nome']
        )
        
        # Opções de visualização
        st.subheader("Opções de Visualização")
        
        # Checkbox para mostrar projeções
        mostrar_projecoes = st.checkbox("Mostrar projeções", value=True)
        
        # Slider para horizonte de projeção
        if mostrar_projecoes:
            horizonte_projecao = st.slider(
                "Horizonte de projeção (anos):",
                min_value=1,
                max_value=5,
                value=2,
                step=1
            )
        else:
            horizonte_projecao = 2
        
        # Checkbox para mostrar eventos significativos
        mostrar_eventos = st.checkbox("Mostrar eventos significativos", value=True)
        
        # Checkbox para normalizar valores em comparações
        normalizar_comparacoes = st.checkbox("Normalizar valores em comparações", value=False)
    
    # Carregar dados se não estiverem na sessão
    if 'dados_indicadores' not in st.session_state:
        with st.spinner("Carregando dados..."):
            dados_indicadores = carregar_dados()
            st.session_state['dados_indicadores'] = dados_indicadores
    else:
        dados_indicadores = st.session_state['dados_indicadores']
    
    # Filtrar dados pelo período selecionado
    dados_filtrados = {}
    for id_indicador, df in dados_indicadores.items():
        if not df.empty and 'data' in df.columns:
            mask = df['data'].dt.year.isin(anos_selecionados)
            dados_filtrados[id_indicador] = df[mask].copy()
        else:
            dados_filtrados[id_indicador] = pd.DataFrame()
    
    # Criar abas para diferentes visualizações
    tab_visao_geral, tab_detalhes, tab_comparativo, tab_previsoes, tab_exportar = st.tabs([
        "Visão Geral", "Detalhes", "Comparativo", "Previsões", "Exportar Dados"
    ])
    
    # Instanciar componentes de visualização
    exibidor_metricas = ExibidorMetricas()
    exibidor_graficos = ExibidorGraficos()
    exportador = Exportador()
    
    # Aba de Visão Geral
    with tab_visao_geral:
        # Banner principal
        st.image(os.path.join(DIRETORIO_ICONES, "banner 2.png"), use_column_width=True)
        
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
            cols = st.columns(len(indicadores_selecionados) if indicadores_selecionados else 1)
            
            # Exibir métricas para cada indicador selecionado
            for i, id_indicador in enumerate(indicadores_selecionados):
                if id_indicador in dados_filtrados and not dados_filtrados[id_indicador].empty:
                    with cols[i % len(cols)]:
                        # Obter configuração do indicador
                        config_ind = config_indicadores[id_indicador]
                        
                        # Exibir ícone se disponível
                        icone_path = os.path.join(DIRETORIO_ICONES, config_ind['icone'])
                        if os.path.exists(icone_path):
                            st.image(icone_path, width=50)
                        
                        # Exibir métrica
                        exibidor_metricas.exibir_metrica_indicador(
                            dados_filtrados[id_indicador], 
                            config_ind['nome'], 
                            config_ind['unidade'],
                            config_ind['formato']
                        )
        else:
            st.info("Nenhum dado disponível para exibição de métricas.")
        
        # Gráfico principal
        st.header("Visualização Histórica de Indicadores Macroeconômicos")
        
        # Seleção do indicador principal
        id_indicador_principal = st.selectbox(
            "Selecione o indicador principal:",
            options=indicadores_selecionados if indicadores_selecionados else list(config_indicadores.keys()),
            format_func=lambda x: config_indicadores[x]['nome']
        )
        
        # Verificar se há dados para o indicador selecionado
        if id_indicador_principal in dados_filtrados and not dados_filtrados[id_indicador_principal].empty:
            # Obter configuração do indicador
            config_ind = config_indicadores[id_indicador_principal]
            
            # Exibir gráfico
            exibidor_graficos.exibir_serie_temporal(
                dados_filtrados[id_indicador_principal],
                f"Evolução de {config_ind['nome']} ({config_ind['unidade']})",
                config_ind['cor'],
                mostrar_eventos=mostrar_eventos
            )
        else:
            st.info(f"Não há dados disponíveis para {config_indicadores[id_indicador_principal]['nome']} no período selecionado.")
    
    # Aba de Detalhes
    with tab_detalhes:
        st.header("Análise Detalhada por Indicador")
        
        # Seleção do indicador para análise detalhada
        id_indicador_detalhes = st.selectbox(
            "Selecione o indicador para análise detalhada:",
            options=indicadores_selecionados if indicadores_selecionados else list(config_indicadores.keys()),
            format_func=lambda x: config_indicadores[x]['nome'],
            key="detalhes_indicador"
        )
        
        # Verificar se há dados para o indicador selecionado
        if id_indicador_detalhes in dados_filtrados and not dados_filtrados[id_indicador_detalhes].empty:
            # Obter configuração do indicador
            config_ind = config_indicadores[id_indicador_detalhes]
            
            # Exibir estatísticas descritivas
            st.subheader(f"Estatísticas de {config_ind['nome']}")
            
            # Criar colunas para estatísticas e gráfico
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Exibir estatísticas
                exibidor_metricas.exibir_estatisticas_indicador(
                    dados_filtrados[id_indicador_detalhes],
                    config_ind['formato']
                )
                
                # Exibir informações adicionais
                st.info(f"""
                **Descrição:** {config_ind['descricao']}
                
                **Fonte:** {config_ind['fonte']}
                
                **Unidade:** {config_ind['unidade']}
                """)
            
            with col2:
                # Exibir gráfico de distribuição
                exibidor_graficos.exibir_distribuicao(
                    dados_filtrados[id_indicador_detalhes],
                    f"Distribuição de {config_ind['nome']}",
                    config_ind['cor']
                )
            
            # Exibir gráfico de tendência com média móvel
            st.subheader(f"Tendência de {config_ind['nome']}")
            exibidor_graficos.exibir_tendencia(
                dados_filtrados[id_indicador_detalhes],
                f"Tendência de {config_ind['nome']} com Média Móvel",
                config_ind['cor']
            )
            
            # Exibir eventos significativos se solicitado
            if mostrar_eventos:
                st.subheader(f"Eventos Significativos em {config_ind['nome']}")
                
                # Detectar eventos para o indicador selecionado
                detector = DetectorEventos()
                df_eventos = detector.detectar_eventos(dados_filtrados[id_indicador_detalhes])
                
                if not df_eventos.empty:
                    # Exibir gráfico com eventos
                    exibidor_graficos.exibir_eventos(
                        dados_filtrados[id_indicador_detalhes],
                        df_eventos,
                        f"Eventos Significativos em {config_ind['nome']}",
                        config_ind['cor']
                    )
                else:
                    st.info(f"Nenhum evento significativo detectado para {config_ind['nome']} no período selecionado.")
        else:
            st.info(f"Não há dados disponíveis para {config_indicadores[id_indicador_detalhes]['nome']} no período selecionado.")
    
    # Aba de Comparativo
    with tab_comparativo:
        st.header("Análise de Correlação entre Indicadores")
        
        # Verificar se há indicadores suficientes selecionados
        if len(indicadores_selecionados) >= 2:
            # Filtrar apenas indicadores com dados
            indicadores_com_dados = [
                id_ind for id_ind in indicadores_selecionados 
                if id_ind in dados_filtrados and not dados_filtrados[id_ind].empty
            ]
            
            if len(indicadores_com_dados) >= 2:
                # Exibir matriz de correlação
                exibidor_graficos.exibir_correlacao(
                    dados_filtrados,
                    config_indicadores,
                    anos_selecionados
                )
                
                # Exibir gráfico de comparação
                st.subheader("Comparação entre Indicadores")
                
                # Seleção dos indicadores para comparação
                col1, col2 = st.columns(2)
                
                with col1:
                    id_indicador1 = st.selectbox(
                        "Selecione o primeiro indicador:",
                        options=indicadores_com_dados,
                        format_func=lambda x: config_indicadores[x]['nome'],
                        key="comparacao_indicador1"
                    )
                
                with col2:
                    # Filtrar o segundo indicador para não ser igual ao primeiro
                    opcoes_indicador2 = [id_ind for id_ind in indicadores_com_dados if id_ind != id_indicador1]
                    id_indicador2 = st.selectbox(
                        "Selecione o segundo indicador:",
                        options=opcoes_indicador2,
                        format_func=lambda x: config_indicadores[x]['nome'],
                        key="comparacao_indicador2"
                    )
                
                # Exibir gráfico de comparação
                exibidor_graficos.exibir_comparacao(
                    dados_filtrados[id_indicador1],
                    dados_filtrados[id_indicador2],
                    config_indicadores[id_indicador1],
                    config_indicadores[id_indicador2],
                    normalizar=normalizar_comparacoes
                )
                
                # Exibir gráfico de dispersão
                st.subheader("Análise de Dispersão")
                exibidor_graficos.exibir_dispersao(
                    dados_filtrados[id_indicador1],
                    dados_filtrados[id_indicador2],
                    config_indicadores[id_indicador1]['nome'],
                    config_indicadores[id_indicador2]['nome']
                )
            else:
                st.info("São necessários pelo menos dois indicadores com dados para análise de correlação.")
        else:
            st.info("Selecione pelo menos dois indicadores para análise de correlação.")
    
    # Aba de Previsões
    with tab_previsoes:
        st.header("Previsão de Indicadores")
        
        # Verificar se há indicadores selecionados
        if indicadores_selecionados:
            # Filtrar apenas indicadores com dados
            indicadores_com_dados = [
                id_ind for id_ind in indicadores_selecionados 
                if id_ind in dados_filtrados and not dados_filtrados[id_ind].empty
            ]
            
            if indicadores_com_dados:
                # Seleção do indicador para previsão
                id_indicador_previsao = st.selectbox(
                    "Selecione o indicador para previsão:",
                    options=indicadores_com_dados,
                    format_func=lambda x: config_indicadores[x]['nome'],
                    key="previsao_indicador"
                )
                
                # Exibir imagem de previsão
                st.image(os.path.join(DIRETORIO_ICONES, "previsao.png"), width=100)
                
                # Verificar se há dados suficientes para previsão
                if len(dados_filtrados[id_indicador_previsao]) >= 12:  # Pelo menos 12 pontos para previsão
                    # Gerar previsão
                    previsor = PrevisorSeriesTemporal()
                    df_previsao = previsor.gerar_previsao(
                        dados_filtrados[id_indicador_previsao],
                        horizonte_projecao * 12  # Converter anos para meses
                    )
                    
                    if not df_previsao.empty:
                        # Exibir gráfico de previsão
                        exibidor_graficos.exibir_previsao(
                            dados_filtrados[id_indicador_previsao],
                            df_previsao,
                            f"Previsão de {config_indicadores[id_indicador_previsao]['nome']} para {horizonte_projecao} anos",
                            config_indicadores[id_indicador_previsao]['cor']
                        )
                        
                        # Exibir tabela com valores previstos
                        with st.expander("Ver valores previstos"):
                            exibidor_metricas.exibir_tabela_previsao(
                                df_previsao,
                                config_indicadores[id_indicador_previsao]['formato']
                            )
                    else:
                        st.warning("Não foi possível gerar previsão para este indicador.")
                else:
                    st.warning(f"Dados insuficientes para gerar previsão de {config_indicadores[id_indicador_previsao]['nome']}. São necessários pelo menos 12 pontos de dados.")
            else:
                st.info("Não há indicadores disponíveis para previsão.")
        else:
            st.info("Selecione pelo menos um indicador para previsão.")
    
    # Aba de Exportação de Dados
    with tab_exportar:
        st.header("Exportar Dados")
        
        # Verificar se há indicadores selecionados
        if indicadores_selecionados:
            # Filtrar apenas indicadores com dados
            indicadores_com_dados = [
                id_ind for id_ind in indicadores_selecionados 
                if id_ind in dados_filtrados and not dados_filtrados[id_ind].empty
            ]
            
            if indicadores_com_dados:
                # Seleção dos indicadores para exportação
                indicadores_exportacao = st.multiselect(
                    "Selecione os indicadores para exportação:",
                    options=indicadores_com_dados,
                    default=indicadores_com_dados,
                    format_func=lambda x: config_indicadores[x]['nome'],
                    key="exportacao_indicadores"
                )
                
                if indicadores_exportacao:
                    # Seleção do formato de exportação
                    formato_exportacao = st.radio(
                        "Selecione o formato de exportação:",
                        options=["CSV"],
                        horizontal=True
                    )
                    
                    # Botão para exportar
                    if st.button("📥 Exportar Dados"):
                        # Preparar dados para exportação
                        dados_exportacao = {}
                        for id_ind in indicadores_exportacao:
                            dados_exportacao[id_ind] = dados_filtrados[id_ind]
                        
                        # Exportar dados
                        if formato_exportacao == "CSV":
                            for id_ind, df in dados_exportacao.items():
                                nome_arquivo = f"{id_ind}_{min(anos_selecionados)}-{max(anos_selecionados)}.csv"
                                exportador.exportar_csv(df, nome_arquivo)
                                st.success(f"Dados de {config_indicadores[id_ind]['nome']} exportados com sucesso para {nome_arquivo}!")
                                
                                # Botão para download
                                st.download_button(
                                    label=f"Baixar {config_indicadores[id_ind]['nome']}",
                                    data=exportador.gerar_csv_string(df),
                                    file_name=nome_arquivo,
                                    mime="text/csv"
                                )
                else:
                    st.info("Selecione pelo menos um indicador para exportação.")
            else:
                st.info("Não há indicadores disponíveis para exportação.")
        else:
            st.info("Selecione pelo menos um indicador para exportação.")

# Executar o dashboard
if __name__ == "__main__":
    main()
