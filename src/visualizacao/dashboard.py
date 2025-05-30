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
            "Selecione os indicadores para visualização:",
            options=list(config_indicadores.keys()),
            default=['pib', 'desemprego', 'ipca'],
            format_func=lambda x: config_indicadores[x]['nome']
        )
        
        # Opções adicionais
        st.subheader("Opções")
        
        # Opção para mostrar eventos significativos
        mostrar_eventos = st.checkbox("Mostrar eventos significativos", value=True)
        
        # Opção para mostrar projeções
        mostrar_projecoes = st.checkbox("Mostrar projeções futuras", value=True)
    
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
            # Adicionar coluna de ano
            df['ano'] = df['data'].dt.year
            
            # Filtrar por anos selecionados
            df_filtrado = df[df['ano'].isin(anos_selecionados)]
            
            # Remover coluna de ano (temporária)
            df_filtrado = df_filtrado.drop(columns=['ano'])
            
            dados_filtrados[id_indicador] = df_filtrado
        else:
            dados_filtrados[id_indicador] = df
    
    # Detectar eventos se solicitado
    eventos_indicadores = {}
    if mostrar_eventos:
        eventos_indicadores = detectar_eventos_indicadores(dados_filtrados)
    
    # Gerar projeções se solicitado
    projecoes_indicadores = {}
    if mostrar_projecoes:
        try:
            projecoes_indicadores = gerar_previsoes_para_indicadores(dados_filtrados)
        except Exception as e:
            logger.error(f"Erro ao gerar projeções: {str(e)}")
            st.warning("Não foi possível gerar projeções. Verifique os dados e tente novamente.")
    
    # Inicializar componentes de visualização
    exibidor_metricas = ExibidorMetricas(diretorio_icones=DIRETORIO_ICONES)
    exibidor_graficos = ExibidorGraficos()
    exportador = Exportador()
    
    # Criar abas
    tab_visao_geral, tab_detalhes, tab_comparativo, tab_previsoes, tab_exportar = st.tabs([
        "Visão Geral", "Detalhes", "Comparativo", "Previsões", "Exportar Dados"
    ])
    
    # Aba de Visão Geral
    with tab_visao_geral:
        # Banner
        banner_path = os.path.join(DIRETORIO_ICONES, "banner 2.png")
        if os.path.exists(banner_path):
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
                            st.image(icone_path, width=50, use_container_width=False)
                        
                        # Exibir métrica usando st.metric diretamente
                        try:
                            # Obter o último valor
                            df = dados_filtrados[id_indicador]
                            if not df.empty and 'data' in df.columns:
                                ultima_linha = df.iloc[-1]
                                ultima_data = ultima_linha['data']
                                
                                # Determinar a coluna de valor
                                coluna_valor = None
                                if 'valor' in df.columns:
                                    coluna_valor = 'valor'
                                elif 'deficit' in df.columns:
                                    coluna_valor = 'deficit'
                                elif 'iof' in df.columns:
                                    coluna_valor = 'iof'
                                else:
                                    # Encontrar a primeira coluna numérica que não seja 'data'
                                    colunas_numericas = [col for col in df.columns if col != 'data' and pd.api.types.is_numeric_dtype(df[col])]
                                    if colunas_numericas:
                                        coluna_valor = colunas_numericas[0]
                                
                                # Verificar se encontrou uma coluna de valor
                                if coluna_valor is not None:
                                    # Obter e formatar o valor
                                    valor = ultima_linha[coluna_valor]
                                    valor_formatado = config_ind['formato'].format(valor)
                                    
                                    # Exibir a métrica
                                    st.metric(
                                        label=config_ind['nome'],
                                        value=valor_formatado,
                                        delta=None,
                                        help=f"Última atualização: {ultima_data.strftime('%d/%m/%Y')}"
                                    )
                                    
                                    # Exibir informação adicional
                                    st.caption(f"Unidade: {config_ind['unidade']}")
                                else:
                                    st.warning(f"Não foi possível determinar a coluna de valor para {config_ind['nome']}")
                            else:
                                st.warning(f"Dados insuficientes para {config_ind['nome']}")
                        except Exception as e:
                            logger.error(f"Erro ao exibir métrica para {config_ind['nome']}: {str(e)}")
                            st.warning(f"Erro ao exibir métrica para {config_ind['nome']}")
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
                try:
                    # Determinar a coluna de valor
                    coluna_valor = None
                    df = dados_filtrados[id_indicador_detalhes]
                    
                    if 'valor' in df.columns:
                        coluna_valor = 'valor'
                    elif 'deficit' in df.columns:
                        coluna_valor = 'deficit'
                    elif 'iof' in df.columns:
                        coluna_valor = 'iof'
                    else:
                        # Encontrar a primeira coluna numérica que não seja 'data'
                        colunas_numericas = [col for col in df.columns if col != 'data' and pd.api.types.is_numeric_dtype(df[col])]
                        if colunas_numericas:
                            coluna_valor = colunas_numericas[0]
                    
                    if coluna_valor:
                        # Criar histograma
                        fig = px.histogram(
                            df, 
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
            
            # Determinar a coluna de valor
            coluna_valor = None
            df = dados_filtrados[id_indicador_detalhes]
            
            if 'valor' in df.columns:
                coluna_valor = 'valor'
            elif 'deficit' in df.columns:
                coluna_valor = 'deficit'
            elif 'iof' in df.columns:
                coluna_valor = 'iof'
            else:
                # Encontrar a primeira coluna numérica que não seja 'data'
                colunas_numericas = [col for col in df.columns if col != 'data' and pd.api.types.is_numeric_dtype(df[col])]
                if colunas_numericas:
                    coluna_valor = colunas_numericas[0]
            
            if coluna_valor:
                # Criar tabela simplificada
                df_exibicao = df[['data', coluna_valor]].copy()
                df_exibicao.columns = ['Data', config_ind['nome']]
                
                # Formatar valores
                df_exibicao[config_ind['nome']] = df_exibicao[config_ind['nome']].apply(
                    lambda x: config_ind['formato'].format(x)
                )
                
                # Formatar datas
                df_exibicao['Data'] = df_exibicao['Data'].dt.strftime('%d/%m/%Y')
                
                # Ordenar por data (mais recente primeiro)
                df_exibicao = df_exibicao.sort_values('Data', ascending=False)
                
                # Exibir tabela
                st.dataframe(df_exibicao, use_container_width=True)
            else:
                st.warning("Não foi possível determinar a coluna de valor para a tabela")
        else:
            st.info(f"Não há dados disponíveis para {config_indicadores[id_indicador_detalhes]['nome']} no período selecionado.")
    
    # Aba de Comparativo
    with tab_comparativo:
        st.header("Comparativo entre Indicadores")
        
        # Verificar se há pelo menos dois indicadores selecionados
        if len(indicadores_selecionados) < 2:
            st.warning("Selecione pelo menos dois indicadores para comparação.")
        else:
            # Seleção dos indicadores para comparação
            col1, col2 = st.columns(2)
            
            with col1:
                id_indicador_comp1 = st.selectbox(
                    "Selecione o primeiro indicador:",
                    options=indicadores_selecionados,
                    format_func=lambda x: config_indicadores[x]['nome'],
                    key="comp_ind1"
                )
            
            with col2:
                # Filtrar para não permitir selecionar o mesmo indicador duas vezes
                opcoes_restantes = [id for id in indicadores_selecionados if id != id_indicador_comp1]
                id_indicador_comp2 = st.selectbox(
                    "Selecione o segundo indicador:",
                    options=opcoes_restantes,
                    format_func=lambda x: config_indicadores[x]['nome'],
                    key="comp_ind2"
                )
            
            # Verificar se há dados para os indicadores selecionados
            if (id_indicador_comp1 in dados_filtrados and not dados_filtrados[id_indicador_comp1].empty and
                id_indicador_comp2 in dados_filtrados and not dados_filtrados[id_indicador_comp2].empty):
                
                # Obter configurações dos indicadores
                config_ind1 = config_indicadores[id_indicador_comp1]
                config_ind2 = config_indicadores[id_indicador_comp2]
                
                # Exibir gráfico de comparação
                st.subheader(f"Comparação: {config_ind1['nome']} vs {config_ind2['nome']}")
                
                # Criar gráfico de comparação
                try:
                    # Obter DataFrames
                    df1 = dados_filtrados[id_indicador_comp1].copy()
                    df2 = dados_filtrados[id_indicador_comp2].copy()
                    
                    # Determinar colunas de valor
                    coluna_valor1 = None
                    if 'valor' in df1.columns:
                        coluna_valor1 = 'valor'
                    elif 'deficit' in df1.columns:
                        coluna_valor1 = 'deficit'
                    elif 'iof' in df1.columns:
                        coluna_valor1 = 'iof'
                    else:
                        # Encontrar a primeira coluna numérica que não seja 'data'
                        colunas_numericas = [col for col in df1.columns if col != 'data' and pd.api.types.is_numeric_dtype(df1[col])]
                        if colunas_numericas:
                            coluna_valor1 = colunas_numericas[0]
                    
                    coluna_valor2 = None
                    if 'valor' in df2.columns:
                        coluna_valor2 = 'valor'
                    elif 'deficit' in df2.columns:
                        coluna_valor2 = 'deficit'
                    elif 'iof' in df2.columns:
                        coluna_valor2 = 'iof'
                    else:
                        # Encontrar a primeira coluna numérica que não seja 'data'
                        colunas_numericas = [col for col in df2.columns if col != 'data' and pd.api.types.is_numeric_dtype(df2[col])]
                        if colunas_numericas:
                            coluna_valor2 = colunas_numericas[0]
                    
                    if coluna_valor1 and coluna_valor2:
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
                        df_mesclado = pd.merge(df1, df2, on='data', suffixes=('_1', '_2'))
                        
                        if not df_mesclado.empty:
                            # Calcular correlação
                            correlacao = df_mesclado[f"{coluna_valor1}_1"].corr(df_mesclado[f"{coluna_valor2}_2"])
                            
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
                            fig_scatter = px.scatter(
                                df_mesclado, 
                                x=f"{coluna_valor1}_1", 
                                y=f"{coluna_valor2}_2",
                                trendline="ols",
                                labels={
                                    f"{coluna_valor1}_1": f"{config_ind1['nome']} ({config_ind1['unidade']})",
                                    f"{coluna_valor2}_2": f"{config_ind2['nome']} ({config_ind2['unidade']})"
                                },
                                title=f"Dispersão: {config_ind1['nome']} vs {config_ind2['nome']}"
                            )
                            
                            # Exibir gráfico
                            st.plotly_chart(fig_scatter, use_container_width=True)
                        else:
                            st.warning("Não há dados com datas coincidentes para os indicadores selecionados.")
                    else:
                        st.warning("Não foi possível determinar as colunas de valor para comparação")
                except Exception as e:
                    logger.error(f"Erro ao exibir comparação: {str(e)}")
                    st.warning("Erro ao exibir comparação entre indicadores")
            else:
                st.info("Não há dados disponíveis para os indicadores selecionados no período selecionado.")
    
    # Aba de Previsões
    with tab_previsoes:
        st.header("Projeções Futuras")
        
        if not mostrar_projecoes:
            st.info("Ative a opção 'Mostrar projeções futuras' no painel lateral para visualizar as projeções.")
        else:
            # Seleção do indicador para projeção
            id_indicador_prev = st.selectbox(
                "Selecione o indicador para projeção:",
                options=indicadores_selecionados if indicadores_selecionados else list(config_indicadores.keys()),
                format_func=lambda x: config_indicadores[x]['nome'],
                key="prev_ind"
            )
            
            # Verificar se há projeções para o indicador selecionado
            if id_indicador_prev in projecoes_indicadores and not projecoes_indicadores[id_indicador_prev].empty:
                # Obter configuração do indicador
                config_ind = config_indicadores[id_indicador_prev]
                
                # Exibir gráfico de projeção
                st.subheader(f"Projeção de {config_ind['nome']} para os próximos 2 anos")
                
                # Obter DataFrames
                df_historico = dados_filtrados[id_indicador_prev].copy() if id_indicador_prev in dados_filtrados else pd.DataFrame()
                df_projecao = projecoes_indicadores[id_indicador_prev].copy()
                
                # Determinar colunas de valor
                coluna_valor_hist = None
                if not df_historico.empty:
                    if 'valor' in df_historico.columns:
                        coluna_valor_hist = 'valor'
                    elif 'deficit' in df_historico.columns:
                        coluna_valor_hist = 'deficit'
                    elif 'iof' in df_historico.columns:
                        coluna_valor_hist = 'iof'
                    else:
                        # Encontrar a primeira coluna numérica que não seja 'data'
                        colunas_numericas = [col for col in df_historico.columns if col != 'data' and pd.api.types.is_numeric_dtype(df_historico[col])]
                        if colunas_numericas:
                            coluna_valor_hist = colunas_numericas[0]
                
                # Criar figura
                fig = go.Figure()
                
                # Adicionar dados históricos
                if not df_historico.empty and coluna_valor_hist:
                    fig.add_trace(go.Scatter(
                        x=df_historico['data'],
                        y=df_historico[coluna_valor_hist],
                        name="Dados Históricos",
                        line=dict(color=config_ind['cor'])
                    ))
                
                # Adicionar projeção
                fig.add_trace(go.Scatter(
                    x=df_projecao['ds'],
                    y=df_projecao['yhat'],
                    name="Projeção",
                    line=dict(color='rgba(0, 0, 255, 0.8)', dash='dash')
                ))
                
                # Adicionar intervalo de confiança
                fig.add_trace(go.Scatter(
                    x=df_projecao['ds'].tolist() + df_projecao['ds'].tolist()[::-1],
                    y=df_projecao['yhat_upper'].tolist() + df_projecao['yhat_lower'].tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(0, 0, 255, 0.1)',
                    line=dict(color='rgba(255, 255, 255, 0)'),
                    name="Intervalo de Confiança (95%)"
                ))
                
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
                
                # Criar tabela de projeções
                df_tabela = df_projecao[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
                df_tabela.columns = ['Data', 'Projeção', 'Limite Inferior', 'Limite Superior']
                
                # Formatar valores
                for col in ['Projeção', 'Limite Inferior', 'Limite Superior']:
                    df_tabela[col] = df_tabela[col].apply(
                        lambda x: config_ind['formato'].format(x)
                    )
                
                # Formatar datas
                df_tabela['Data'] = df_tabela['Data'].dt.strftime('%d/%m/%Y')
                
                # Ordenar por data (mais próxima primeiro)
                df_tabela = df_tabela.sort_values('Data')
                
                # Exibir tabela
                st.dataframe(df_tabela, use_container_width=True)
                
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
            else:
                st.info(f"Não foi possível gerar projeções para {config_indicadores[id_indicador_prev]['nome']}. Verifique se há dados históricos suficientes.")
    
    # Aba de Exportação
    with tab_exportar:
        st.header("Exportar Dados")
        
        # Seleção do indicador para exportação
        id_indicador_exp = st.selectbox(
            "Selecione o indicador para exportação:",
            options=indicadores_selecionados if indicadores_selecionados else list(config_indicadores.keys()),
            format_func=lambda x: config_indicadores[x]['nome'],
            key="exp_ind"
        )
        
        # Verificar se há dados para o indicador selecionado
        if id_indicador_exp in dados_filtrados and not dados_filtrados[id_indicador_exp].empty:
            # Obter configuração do indicador
            config_ind = config_indicadores[id_indicador_exp]
            
            # Exibir opções de exportação
            st.subheader("Opções de Exportação")
            
            # Seleção do formato
            formato_exp = st.radio(
                "Selecione o formato de exportação:",
                options=["CSV", "Excel", "JSON"],
                horizontal=True
            )
            
            # Opção para incluir projeções
            incluir_projecoes = st.checkbox(
                "Incluir projeções",
                value=True if mostrar_projecoes and id_indicador_exp in projecoes_indicadores else False,
                disabled=not (mostrar_projecoes and id_indicador_exp in projecoes_indicadores)
            )
            
            # Botão de exportação
            if st.button("Exportar Dados"):
                try:
                    # Obter DataFrame
                    df_exp = dados_filtrados[id_indicador_exp].copy()
                    
                    # Incluir projeções se solicitado
                    if incluir_projecoes and id_indicador_exp in projecoes_indicadores:
                        df_proj = projecoes_indicadores[id_indicador_exp].copy()
                        
                        # Renomear colunas para padronização
                        df_proj = df_proj.rename(columns={
                            'ds': 'data',
                            'yhat': 'projecao',
                            'yhat_lower': 'limite_inferior',
                            'yhat_upper': 'limite_superior'
                        })
                        
                        # Adicionar coluna de tipo
                        df_exp['tipo'] = 'historico'
                        df_proj['tipo'] = 'projecao'
                        
                        # Selecionar colunas relevantes
                        colunas_valor = [col for col in df_exp.columns if col not in ['data', 'tipo']]
                        
                        # Adicionar colunas de valor às projeções
                        for col in colunas_valor:
                            df_proj[col] = None
                        
                        # Concatenar DataFrames
                        df_exp = pd.concat([df_exp, df_proj], ignore_index=True)
                    
                    # Exportar conforme formato selecionado
                    nome_arquivo = f"{id_indicador_exp}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    if formato_exp == "CSV":
                        # Exportar para CSV
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
                    
                    elif formato_exp == "Excel":
                        # Exportar para Excel
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
                    
                    elif formato_exp == "JSON":
                        # Exportar para JSON
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
                    logger.error(f"Erro ao exportar dados: {str(e)}")
                    st.error(f"Erro ao exportar dados: {str(e)}")
        else:
            st.info(f"Não há dados disponíveis para {config_indicadores[id_indicador_exp]['nome']} no período selecionado.")

# Executar o dashboard
if __name__ == "__main__":
    main()
