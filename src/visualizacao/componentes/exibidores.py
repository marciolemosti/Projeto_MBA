"""
Módulo de componentes de visualização para o dashboard Termômetro da Economia.

Este módulo implementa componentes reutilizáveis para o dashboard,
incluindo exibição de métricas, gráficos e análises.
"""

import os
import logging
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple

logger = logging.getLogger(__name__)

class ExibidorMetricas:
    """Classe para exibição de métricas no dashboard."""
    
    def __init__(self, diretorio_icones: str = None, icon_dir: str = None):
        """
        Inicializa o componente de exibição de métricas.
        
        Args:
            diretorio_icones: Diretório onde os ícones estão armazenados
            icon_dir: Alias para diretorio_icones (compatibilidade)
        """
        self.diretorio_icones = diretorio_icones or icon_dir
        logger.info(f"ExibidorMetricas inicializado com diretório de ícones: {self.diretorio_icones}")
    
    def _carregar_icone(self, nome_icone: str) -> Optional[str]:
        """
        Carrega um ícone do diretório de ícones.
        
        Args:
            nome_icone: Nome do arquivo do ícone
            
        Returns:
            Caminho completo para o ícone ou None se não encontrado
        """
        if not self.diretorio_icones or not nome_icone:
            return None
            
        caminho_icone = os.path.join(self.diretorio_icones, nome_icone)
        if os.path.exists(caminho_icone):
            return caminho_icone
        else:
            logger.warning(f"Ícone não encontrado: {caminho_icone}")
            return None
    
    def exibir_metricas(self, dados_indicadores: Dict[str, pd.DataFrame], 
                       config_indicadores: Dict[str, Dict[str, Any]]) -> None:
        """
        Exibe métricas para os indicadores configurados.
        
        Args:
            dados_indicadores: Dicionário com DataFrames dos indicadores
            config_indicadores: Configuração dos indicadores
        """
        # Filtrar apenas indicadores com dados disponíveis
        indicadores_disponiveis = {k: v for k, v in dados_indicadores.items() if not v.empty}
        
        if not indicadores_disponiveis:
            st.warning("Nenhum dado disponível para exibição de métricas.")
            return
        
        # Criar colunas para as métricas
        colunas = st.columns(len(indicadores_disponiveis))
        
        # Exibir métricas em cada coluna
        for i, (id_indicador, df) in enumerate(indicadores_disponiveis.items()):
            if id_indicador in config_indicadores:
                config = config_indicadores[id_indicador]
                
                # Obter o último valor
                if not df.empty:
                    ultima_linha = df.iloc[-1]
                    ultima_data = ultima_linha['data']
                    
                    # Obter o valor da coluna configurada ou usar a primeira coluna numérica disponível
                    coluna_valor = config.get('coluna_valor')
                    if coluna_valor and coluna_valor in ultima_linha:
                        valor = ultima_linha[coluna_valor]
                    elif 'valor' in ultima_linha:
                        valor = ultima_linha['valor']
                    elif 'deficit' in ultima_linha:
                        valor = ultima_linha['deficit']
                    elif 'iof' in ultima_linha:
                        valor = ultima_linha['iof']
                    else:
                        # Encontrar a primeira coluna numérica que não seja 'data'
                        colunas_numericas = [col for col in df.columns if col != 'data' and pd.api.types.is_numeric_dtype(df[col])]
                        if colunas_numericas:
                            valor = ultima_linha[colunas_numericas[0]]
                        else:
                            valor = None
                    
                    # Aplicar transformação se configurada
                    if valor is not None and 'transformacao_valor' in config:
                        valor = config['transformacao_valor'](valor)
                    
                    # Formatar o valor
                    if valor is not None:
                        formato = config.get('formato', '{:.2f}')
                        valor_formatado = formato.format(valor)
                        
                        # Exibir a métrica
                        with colunas[i]:
                            st.subheader(config.get('nome', id_indicador))
                            
                            # Carregar e exibir ícone se disponível
                            icone = self._carregar_icone(config.get('icone', ''))
                            if icone:
                                st.image(icone, width=50, use_container_width=False)
                            
                            st.markdown(f"<h1 style='text-align: center;'>{valor_formatado}</h1>", unsafe_allow_html=True)
                            st.caption(f"Última atualização: {ultima_data.strftime('%d/%m/%Y')}")
                else:
                    with colunas[i]:
                        st.subheader(config.get('nome', id_indicador))
                        st.warning("Dados não disponíveis")
    
    def exibir_linha_metricas(self, config_metricas: Dict[str, Dict[str, Any]]) -> None:
        """
        Exibe uma linha de métricas com base na configuração fornecida.
        
        Args:
            config_metricas: Configuração das métricas a serem exibidas
        """
        # Criar colunas para as métricas
        colunas = st.columns(len(config_metricas))
        
        # Exibir métricas em cada coluna
        for i, (id_metrica, config) in enumerate(config_metricas.items()):
            with colunas[i]:
                st.subheader(config.get('nome', id_metrica))
                
                # Carregar e exibir ícone se disponível
                icone = self._carregar_icone(config.get('icone', ''))
                if icone:
                    st.image(icone, width=50, use_container_width=False)
                
                # Exibir valor
                valor = config.get('valor', 'N/A')
                st.markdown(f"<h1 style='text-align: center;'>{valor}</h1>", unsafe_allow_html=True)
                
                # Exibir informação adicional
                if 'info' in config:
                    st.caption(config['info'])
    
    def exibir_cabecalho_secao(self, titulo: str, nome_icone: str = None) -> None:
        """
        Exibe um cabeçalho de seção com ícone opcional.
        
        Args:
            titulo: Título da seção
            nome_icone: Nome do arquivo do ícone (opcional)
        """
        col1, col2 = st.columns([0.05, 0.95])
        
        with col1:
            if nome_icone:
                icone = self._carregar_icone(nome_icone)
                if icone:
                    st.image(icone, width=30, use_container_width=False)
        
        with col2:
            st.subheader(titulo)
            
    def exibir_metrica_indicador(self, df: pd.DataFrame, nome: str, unidade: str, formato: str) -> None:
        """
        Exibe uma métrica para um indicador específico.
        
        Args:
            df: DataFrame com os dados do indicador
            nome: Nome do indicador
            unidade: Unidade de medida
            formato: Formato para exibição do valor
        """
        # Verificar se o DataFrame não está vazio
        if df is None or df.empty:
            st.warning(f"Não há dados disponíveis para {nome}")
            return
            
        try:
            # Obter o último valor
            ultima_linha = df.iloc[-1]
            
            # Verificar se a coluna 'data' existe
            if 'data' not in ultima_linha:
                st.warning(f"Coluna 'data' não encontrada para {nome}")
                return
                
            ultima_data = ultima_linha['data']
            
            # Determinar a coluna de valor
            coluna_valor = None
            if 'valor' in ultima_linha:
                coluna_valor = 'valor'
            elif 'deficit' in ultima_linha:
                coluna_valor = 'deficit'
            elif 'iof' in ultima_linha:
                coluna_valor = 'iof'
            else:
                # Encontrar a primeira coluna numérica que não seja 'data'
                colunas_numericas = [col for col in df.columns if col != 'data' and pd.api.types.is_numeric_dtype(df[col])]
                if colunas_numericas:
                    coluna_valor = colunas_numericas[0]
            
            # Verificar se encontrou uma coluna de valor
            if coluna_valor is None:
                st.warning(f"Não foi possível determinar a coluna de valor para {nome}")
                return
                
            # Obter e formatar o valor
            valor = ultima_linha[coluna_valor]
            valor_formatado = formato.format(valor)
            
            # Exibir a métrica
            st.metric(
                label=nome,
                value=valor_formatado,
                delta=None,
                help=f"Última atualização: {ultima_data.strftime('%d/%m/%Y')}"
            )
            
            # Exibir informação adicional
            st.caption(f"Unidade: {unidade}")
            
        except Exception as e:
            logger.error(f"Erro ao exibir métrica para {nome}: {str(e)}")
            st.warning(f"Erro ao exibir métrica para {nome}")
    
    def exibir_estatisticas_indicador(self, df: pd.DataFrame, formato: str) -> None:
        """
        Exibe estatísticas descritivas para um indicador.
        
        Args:
            df: DataFrame com os dados do indicador
            formato: Formato para exibição dos valores
        """
        # Verificar se o DataFrame não está vazio
        if df is None or df.empty:
            st.warning("Não há dados disponíveis para análise estatística")
            return
            
        try:
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
            if coluna_valor is None:
                st.warning("Não foi possível determinar a coluna de valor para análise estatística")
                return
                
            # Calcular estatísticas
            minimo = df[coluna_valor].min()
            maximo = df[coluna_valor].max()
            media = df[coluna_valor].mean()
            mediana = df[coluna_valor].median()
            desvio_padrao = df[coluna_valor].std()
            
            # Formatar valores
            minimo_formatado = formato.format(minimo)
            maximo_formatado = formato.format(maximo)
            media_formatada = formato.format(media)
            mediana_formatada = formato.format(mediana)
            desvio_padrao_formatado = formato.format(desvio_padrao)
            
            # Exibir estatísticas
            st.metric("Mínimo", minimo_formatado)
            st.metric("Máximo", maximo_formatado)
            st.metric("Média", media_formatada)
            st.metric("Mediana", mediana_formatada)
            st.metric("Desvio Padrão", desvio_padrao_formatado)
            
        except Exception as e:
            logger.error(f"Erro ao exibir estatísticas: {str(e)}")
            st.warning("Erro ao calcular estatísticas")


class ExibidorGraficos:
    """Classe para exibição de gráficos no dashboard."""
    
    def __init__(self):
        """Inicializa o componente de exibição de gráficos."""
        logger.info("ExibidorGraficos inicializado")
    
    def exibir_graficos(self, dados_indicadores: Dict[str, pd.DataFrame], 
                      config_indicadores: Dict[str, Dict[str, Any]],
                      anos_selecionados: List[int] = None) -> None:
        """
        Exibe gráficos para os indicadores selecionados.
        
        Args:
            dados_indicadores: Dicionário com DataFrames dos indicadores
            config_indicadores: Configuração dos indicadores
            anos_selecionados: Lista de anos selecionados para filtro
        """
        # Filtrar apenas indicadores com dados disponíveis
        indicadores_disponiveis = {k: v for k, v in dados_indicadores.items() if not v.empty}
        
        if not indicadores_disponiveis:
            st.warning("Nenhum dado disponível para exibição de gráficos.")
            return
        
        # Criar seletor de indicadores
        opcoes_indicadores = [(id_indicador, config.get('nome', id_indicador)) 
                            for id_indicador, config in config_indicadores.items() 
                            if id_indicador in indicadores_disponiveis]
        
        indicador_selecionado = st.selectbox(
            "Selecione o indicador para visualização:",
            [id for id, _ in opcoes_indicadores],
            format_func=lambda x: next((nome for id, nome in opcoes_indicadores if id == x), x)
        )
        
        if indicador_selecionado and indicador_selecionado in indicadores_disponiveis:
            df = indicadores_disponiveis[indicador_selecionado].copy()
            config = config_indicadores[indicador_selecionado]
            
            # Adicionar coluna de ano para filtro
            df['ano'] = df['data'].dt.year
            
            # Filtrar por anos selecionados
            if anos_selecionados:
                df = df[df['ano'].isin(anos_selecionados)]
            
            if not df.empty:
                # Obter configurações do gráfico
                titulo_grafico = config.get('titulo_grafico', f"Evolução de {config.get('nome', indicador_selecionado)}")
                
                # Obter a coluna de valor
                coluna_valor = config.get('coluna_valor')
                if coluna_valor and coluna_valor in df.columns:
                    pass  # Usar a coluna configurada
                elif 'valor' in df.columns:
                    coluna_valor = 'valor'
                elif 'deficit' in df.columns:
                    coluna_valor = 'deficit'
                elif 'iof' in df.columns:
                    coluna_valor = 'iof'
                else:
                    # Encontrar a primeira coluna numérica que não seja 'data', 'ano'
                    colunas_numericas = [col for col in df.columns if col not in ['data', 'ano'] and pd.api.types.is_numeric_dtype(df[col])]
                    if colunas_numericas:
                        coluna_valor = colunas_numericas[0]
                    else:
                        st.error(f"Não foi possível encontrar uma coluna de valor para {config.get('nome', indicador_selecionado)}")
                        return
                
                # Obter labels para o gráfico
                labels_grafico = config.get('labels_grafico', {'data': 'Data', coluna_valor: 'Valor'})
                
                # Criar gráfico
                fig = px.line(
                    df, 
                    x='data', 
                    y=coluna_valor,
                    title=titulo_grafico,
                    labels=labels_grafico
                )
                
                # Configurar formato do eixo Y
                formato_y = config.get('formato_grafico', '.2f')
                fig.update_yaxes(tickformat=formato_y)
                
                # Exibir gráfico
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Não há dados disponíveis para {config.get('nome', indicador_selecionado)} nos anos selecionados.")
    
    def exibir_serie_temporal(self, df: pd.DataFrame, titulo: str, cor: str = None, mostrar_eventos: bool = False) -> None:
        """
        Exibe um gráfico de série temporal para um indicador.
        
        Args:
            df: DataFrame com os dados do indicador
            titulo: Título do gráfico
            cor: Cor da linha do gráfico
            mostrar_eventos: Se deve destacar eventos significativos
        """
        # Verificar se o DataFrame não está vazio
        if df is None or df.empty:
            st.warning("Não há dados disponíveis para exibição do gráfico")
            return
            
        try:
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
            if coluna_valor is None:
                st.warning("Não foi possível determinar a coluna de valor para o gráfico")
                return
                
            # Criar gráfico
            fig = px.line(
                df, 
                x='data', 
                y=coluna_valor,
                title=titulo
            )
            
            # Configurar cor se especificada
            if cor:
                fig.update_traces(line_color=cor)
            
            # Destacar eventos se solicitado
            if mostrar_eventos and 'evento' in df.columns:
                eventos = df[df['evento'] == True]
                if not eventos.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=eventos['data'],
                            y=eventos[coluna_valor],
                            mode='markers',
                            marker=dict(
                                size=10,
                                color='red',
                                symbol='circle'
                            ),
                            name='Eventos Significativos'
                        )
                    )
            
            # Exibir gráfico
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            logger.error(f"Erro ao exibir gráfico: {str(e)}")
            st.warning("Erro ao exibir gráfico de série temporal")
