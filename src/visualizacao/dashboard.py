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

# Configurar página
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
    st.success(f"✅ Caminhos configurados: {PROJETO_ROOT}")
except Exception as e:
    st.error(f"❌ Erro ao configurar caminhos: {e}")
    st.stop()

# Importar sistema de cache e configuração
try:
    from utils.cache import cache_manager, dataframe_cache
    from utils.config import config_manager
    st.success("✅ Utilitários importados com sucesso")
except ImportError as e:
    st.warning(f"⚠️ Utilitários não disponíveis: {e}")
    # Criar mocks básicos
    class MockCache:
        def get(self, key): return None
        def set(self, key, value, ttl=None): pass
        def clear(self): pass
    
    class MockConfig:
        def get(self, key, default=None): return default
    
    cache_manager = MockCache()
    dataframe_cache = MockCache()
    config_manager = MockConfig()

# Importar módulos do projeto
try:
    from dados.extratores.bcb import ExtratorBCB
    from dados.extratores.ibge import ExtratorIBGE
    from dados.processadores.previsao import PrevisorSeriesTemporal
    st.success("✅ Módulos de dados importados com sucesso")
except ImportError as e:
    st.error(f"❌ Erro ao importar módulos de dados: {e}")
    st.info("Verifique se todos os arquivos do projeto estão presentes.")
    
    # Criar classes mock para permitir execução básica
    class MockExtrator:
        def __init__(self, *args, **kwargs): pass
        def extrair_dados(self, *args, **kwargs): return pd.DataFrame()
    
    class MockPrevisor:
        def __init__(self, *args, **kwargs): pass
        def gerar_previsao(self, *args, **kwargs): return pd.DataFrame(), {}
    
    ExtratorBCB = MockExtrator
    ExtratorIBGE = MockExtrator
    PrevisorSeriesTemporal = MockPrevisor
    
    st.warning("⚠️ Executando em modo de demonstração com dados mock")

# Constantes
DIRETORIO_DADOS = os.path.join(PROJETO_ROOT, "data")

def verificar_ambiente():
    """Verifica se o ambiente está configurado corretamente"""
    problemas = []
    
    # Verificar diretório de dados
    if not os.path.exists(DIRETORIO_DADOS):
        problemas.append(f"Diretório de dados não encontrado: {DIRETORIO_DADOS}")
    
    # Verificar arquivos de dados essenciais
    arquivos_essenciais = ['ipca.json', 'selic.json', 'cambio.json']
    for arquivo in arquivos_essenciais:
        caminho = os.path.join(DIRETORIO_DADOS, arquivo)
        if not os.path.exists(caminho):
            problemas.append(f"Arquivo de dados não encontrado: {arquivo}")
    
    return problemas

def carregar_dados() -> Dict[str, pd.DataFrame]:
    """
    Carrega dados dos indicadores econômicos com cache.
    
    Returns:
        Dict[str, pd.DataFrame]: Dicionário com DataFrames dos indicadores
    """
    # Verificar cache primeiro
    dados_cache = cache_manager.get("dados_indicadores")
    if dados_cache is not None:
        logger.info("Dados carregados do cache")
        return dados_cache
    
    logger.info("Carregando dados dos arquivos...")
    
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
    
    # Mapeamento de indicadores para arquivos
    arquivos_dados = {
        'ipca': 'ipca.json',
        'selic': 'selic.json',
        'cambio': 'cambio.json',
        'deficit_primario': 'deficit_primario.json',
        'iof': 'arrecadacao_iof.json',
        'pib': 'pib.json',
        'desemprego': 'desemprego.json'
    }
    
    # Carregar cada arquivo
    for id_indicador, nome_arquivo in arquivos_dados.items():
        try:
            caminho_arquivo = os.path.join(DIRETORIO_DADOS, nome_arquivo)
            
            if os.path.exists(caminho_arquivo):
                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    dados_json = json.load(f)
                
                if dados_json:
                    df = pd.DataFrame(dados_json)
                    if 'data' in df.columns:
                        df['data'] = pd.to_datetime(df['data'])
                        df = df.sort_values('data')
                    dados_indicadores[id_indicador] = df
                    logger.info(f"Carregados {len(df)} registros para {id_indicador}")
                else:
                    logger.warning(f"Arquivo vazio para {id_indicador}")
            else:
                logger.warning(f"Arquivo não encontrado para {id_indicador}: {caminho_arquivo}")
                
        except Exception as e:
            logger.error(f"Erro ao carregar dados de {id_indicador}: {e}")
    
    # Salvar no cache por 1 hora
    cache_manager.set("dados_indicadores", dados_indicadores, ttl=3600)
    
    return dados_indicadores

def obter_coluna_valor(df: pd.DataFrame, indicador: str) -> str:
    """
    Determina qual coluna usar para valores baseado no indicador e colunas disponíveis.
    
    Args:
        df: DataFrame com os dados
        indicador: Nome do indicador
        
    Returns:
        str: Nome da coluna a usar para valores
    """
    if df.empty:
        return 'valor'
    
    colunas = df.columns.tolist()
    
    # Mapeamento preferencial por indicador
    mapeamento_colunas = {
        'ipca': ['valor', 'variacao_mensal', 'indice'],
        'selic': ['valor', 'taxa', 'meta_selic'],
        'cambio': ['valor', 'cotacao_compra', 'cotacao_venda', 'cotacao'],
        'deficit_primario': ['valor', 'resultado', 'deficit'],
        'iof': ['valor', 'arrecadacao', 'receita'],
        'pib': ['valor', 'variacao_trimestral', 'pib_variacao'],
        'desemprego': ['valor', 'taxa_desocupacao', 'taxa']
    }
    
    # Tentar colunas preferenciais para o indicador
    if indicador in mapeamento_colunas:
        for coluna_pref in mapeamento_colunas[indicador]:
            if coluna_pref in colunas:
                return coluna_pref
    
    # Fallback para colunas comuns
    colunas_comuns = ['valor', 'value', 'taxa', 'cotacao', 'indice', 'variacao']
    for coluna_comum in colunas_comuns:
        if coluna_comum in colunas:
            return coluna_comum
    
    # Se nenhuma coluna conhecida, usar a segunda coluna (assumindo primeira é data)
    if len(colunas) > 1:
        return colunas[1]
    
    return 'valor'  # Fallback final

def main():
    """Função principal do dashboard"""
    
    # Verificar ambiente
    problemas = verificar_ambiente()
    if problemas:
        st.error("❌ Problemas detectados no ambiente:")
        for problema in problemas:
            st.write(f"• {problema}")
        st.info("💡 Certifique-se de que está executando a partir do diretório correto do projeto")
        return
    
    # Título principal
    st.title("📊 Termômetro da Economia Brasileira")
    st.markdown("### Dashboard Interativo de Indicadores Econômicos")
    
    # Sidebar com informações
    with st.sidebar:
        st.header("ℹ️ Informações")
        st.write("**Desenvolvido por:** Márcio Lemos")
        st.write("**Projeto:** MBA - Análise Econômica")
        st.write("**Versão:** 2.0.1 (Corrigida)")
        
        # Status do sistema
        st.subheader("🔧 Status do Sistema")
        st.success("✅ Dashboard funcionando")
        st.info(f"📁 Dados: {DIRETORIO_DADOS}")
        
        # Botão para limpar cache
        if st.button("🗑️ Limpar Cache"):
            cache_manager.clear()
            st.success("Cache limpo!")
            st.experimental_rerun()
    
    try:
        # Carregar dados
        with st.spinner("Carregando dados..."):
            dados = carregar_dados()
        
        # Verificar se há dados
        dados_disponiveis = {k: v for k, v in dados.items() if not v.empty}
        
        if not dados_disponiveis:
            st.warning("⚠️ Nenhum dado disponível. Verifique os arquivos de dados.")
            return
        
        st.success(f"✅ Dados carregados: {len(dados_disponiveis)} indicadores")
        
        # Configuração dos indicadores
        config_indicadores = {
            'ipca': {
                'nome': 'IPCA (Amostra)' if 'ipca' in dados_disponiveis else 'IPCA',
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
        
        # Filtrar apenas indicadores disponíveis
        config_indicadores = {k: v for k, v in config_indicadores.items() if k in dados_disponiveis}
        
        # Seletor de indicadores
        st.subheader("📈 Seleção de Indicadores")
        
        indicadores_selecionados = st.multiselect(
            "Escolha os indicadores para visualizar:",
            options=list(config_indicadores.keys()),
            default=list(config_indicadores.keys())[:3],  # Primeiros 3 por padrão
            format_func=lambda x: config_indicadores[x]['nome']
        )
        
        if not indicadores_selecionados:
            st.warning("⚠️ Selecione pelo menos um indicador")
            return
        
        # Visualizações
        st.subheader("📊 Visualizações")
        
        # Criar gráficos para cada indicador selecionado
        for indicador in indicadores_selecionados:
            df = dados[indicador]
            config = config_indicadores[indicador]
            
            if df.empty:
                continue
            
            st.write(f"**{config['nome']}** - {config['descricao']}")
            
            # Determinar coluna de valor
            coluna_valor = obter_coluna_valor(df, indicador)
            
            if coluna_valor not in df.columns:
                st.error(f"Coluna '{coluna_valor}' não encontrada em {indicador}")
                continue
            
            # Criar gráfico
            fig = px.line(
                df, 
                x='data', 
                y=coluna_valor,
                title=f"{config['nome']} ao longo do tempo",
                color_discrete_sequence=[config['cor']]
            )
            
            fig.update_layout(
                xaxis_title="Data",
                yaxis_title=f"{config['nome']} ({config['unidade']})",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas básicas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Último Valor", f"{df[coluna_valor].iloc[-1]:.2f} {config['unidade']}")
            
            with col2:
                variacao = df[coluna_valor].pct_change().iloc[-1] * 100
                st.metric("Variação (%)", f"{variacao:.2f}%")
            
            with col3:
                st.metric("Máximo", f"{df[coluna_valor].max():.2f} {config['unidade']}")
            
            with col4:
                st.metric("Mínimo", f"{df[coluna_valor].min():.2f} {config['unidade']}")
            
            st.divider()
    
    except Exception as e:
        st.error(f"❌ Erro no dashboard: {e}")
        logger.error(f"Erro no dashboard: {e}")
        
        # Informações de debug
        with st.expander("🔍 Informações de Debug"):
            st.write("**Diretório atual:**", os.getcwd())
            st.write("**Diretório do projeto:**", PROJETO_ROOT)
            st.write("**Diretório src:**", SRC_PATH)
            st.write("**Diretório de dados:**", DIRETORIO_DADOS)
            st.write("**Python path:**", sys.path[:5])
    
    # Rodapé
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 20px;'>
            <p><strong>Desenvolvido por Márcio Lemos</strong></p>
            <p>Projeto Final MBA - Termômetro da Economia Brasileira</p>
            
            <details style='margin-top: 20px;'>
                <summary>📊 Fontes dos Dados</summary>
                <div style='margin-top: 10px; text-align: left;'>
                    <h4>Dados Reais:</h4>
                    <ul>
                        <li><strong>IPCA, PIB, Desemprego:</strong> IBGE (Instituto Brasileiro de Geografia e Estatística)</li>
                        <li><strong>Taxa Selic, Câmbio:</strong> BCB (Banco Central do Brasil)</li>
                        <li><strong>Déficit Primário:</strong> Tesouro Nacional / BCB</li>
                        <li><strong>Arrecadação IOF:</strong> Receita Federal do Brasil</li>
                    </ul>
                    <h4>Dados Simulados:</h4>
                    <ul>
                        <li>Modelos de Previsão Estatística</li>
                    </ul>
                </div>
            </details>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
