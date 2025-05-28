"""
Módulo de componentes para exportação de dados do dashboard.

Este módulo implementa classes e funções para exportação de dados
em diferentes formatos (CSV, Excel, etc.).
"""

import os
import pandas as pd
import streamlit as st
import base64
from io import BytesIO, StringIO
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime

# Configuração de logging
logger = logging.getLogger(__name__)

class Exportador:
    """Classe para exportação de dados do dashboard."""
    
    def __init__(self):
        """Inicializa o exportador de dados."""
        logger.info("Exportador inicializado")
    
    def exportar_csv(self, df: pd.DataFrame, nome_arquivo: str = None) -> str:
        """
        Exporta DataFrame para CSV e retorna link para download.
        
        Args:
            df: DataFrame a ser exportado
            nome_arquivo: Nome do arquivo (sem extensão)
            
        Returns:
            Link HTML para download do arquivo
        """
        if df.empty:
            logger.warning("Tentativa de exportar DataFrame vazio")
            return ""
        
        try:
            # Gerar nome de arquivo se não fornecido
            if nome_arquivo is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo = f"dados_economicos_{timestamp}"
            
            # Garantir que tenha extensão .csv
            if not nome_arquivo.endswith('.csv'):
                nome_arquivo += '.csv'
            
            # Converter DataFrame para CSV
            csv = df.to_csv(index=False)
            
            # Codificar em base64
            b64 = base64.b64encode(csv.encode()).decode()
            
            # Criar link para download
            href = f'<a href="data:file/csv;base64,{b64}" download="{nome_arquivo}">Baixar {nome_arquivo}</a>'
            
            logger.info(f"CSV gerado para download: {nome_arquivo}")
            return href
        
        except Exception as e:
            logger.error(f"Erro ao exportar para CSV: {str(e)}")
            return ""
    
    def criar_botao_download_csv(self, df: pd.DataFrame, texto_botao: str = "Baixar dados em CSV", 
                               nome_arquivo: str = None, key: str = None) -> None:
        """
        Cria um botão no Streamlit para download de dados em CSV.
        
        Args:
            df: DataFrame a ser exportado
            texto_botao: Texto a ser exibido no botão
            nome_arquivo: Nome do arquivo (sem extensão)
            key: Chave única para o botão no Streamlit
        """
        if df.empty:
            logger.warning("Tentativa de criar botão para DataFrame vazio")
            st.warning("Não há dados disponíveis para exportação")
            return
        
        try:
            # Gerar nome de arquivo se não fornecido
            if nome_arquivo is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo = f"dados_economicos_{timestamp}"
            
            # Garantir que tenha extensão .csv
            if not nome_arquivo.endswith('.csv'):
                nome_arquivo += '.csv'
            
            # Converter DataFrame para CSV
            csv = df.to_csv(index=False)
            
            # Criar botão de download
            st.download_button(
                label=texto_botao,
                data=csv,
                file_name=nome_arquivo,
                mime='text/csv',
                key=key or f"download_csv_{nome_arquivo}"
            )
            
            logger.info(f"Botão de download CSV criado: {nome_arquivo}")
        
        except Exception as e:
            logger.error(f"Erro ao criar botão de download CSV: {str(e)}")
            st.error("Erro ao gerar arquivo para download")
    
    def exportar_multiplos_dataframes(self, dfs: Dict[str, pd.DataFrame], 
                                    prefixo_arquivo: str = "dados_economicos") -> Dict[str, str]:
        """
        Exporta múltiplos DataFrames para CSV e retorna links para download.
        
        Args:
            dfs: Dicionário com nome do indicador e DataFrame correspondente
            prefixo_arquivo: Prefixo para os nomes dos arquivos
            
        Returns:
            Dicionário com nome do indicador e link HTML para download
        """
        if not dfs:
            logger.warning("Tentativa de exportar dicionário vazio de DataFrames")
            return {}
        
        links = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for nome, df in dfs.items():
            if df.empty:
                logger.warning(f"DataFrame vazio para {nome}, pulando exportação")
                continue
            
            nome_arquivo = f"{prefixo_arquivo}_{nome}_{timestamp}.csv"
            link = self.exportar_csv(df, nome_arquivo)
            
            if link:
                links[nome] = link
        
        return links
    
    def criar_botao_download_todos(self, dfs: Dict[str, pd.DataFrame], 
                                 texto_botao: str = "Baixar todos os dados em CSV",
                                 prefixo_arquivo: str = "dados_economicos") -> None:
        """
        Cria um botão para download de todos os DataFrames em um único arquivo CSV.
        
        Args:
            dfs: Dicionário com nome do indicador e DataFrame correspondente
            texto_botao: Texto a ser exibido no botão
            prefixo_arquivo: Prefixo para o nome do arquivo
        """
        if not dfs:
            logger.warning("Tentativa de criar botão para dicionário vazio de DataFrames")
            st.warning("Não há dados disponíveis para exportação")
            return
        
        try:
            # Filtrar DataFrames não vazios
            dfs_validos = {nome: df for nome, df in dfs.items() if not df.empty}
            
            if not dfs_validos:
                logger.warning("Nenhum DataFrame válido para exportação")
                st.warning("Não há dados disponíveis para exportação")
                return
            
            # Gerar nome de arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"{prefixo_arquivo}_completo_{timestamp}.csv"
            
            # Criar buffer para armazenar todos os dados
            buffer = StringIO()
            
            # Escrever cada DataFrame no buffer
            for nome, df in dfs_validos.items():
                buffer.write(f"# {nome}\n")
                df.to_csv(buffer, index=False)
                buffer.write("\n\n")
            
            # Obter conteúdo do buffer
            csv_data = buffer.getvalue()
            
            # Criar botão de download
            st.download_button(
                label=texto_botao,
                data=csv_data,
                file_name=nome_arquivo,
                mime='text/csv',
                key=f"download_all_csv_{timestamp}"
            )
            
            logger.info(f"Botão de download para todos os dados criado: {nome_arquivo}")
        
        except Exception as e:
            logger.error(f"Erro ao criar botão de download para todos os dados: {str(e)}")
            st.error("Erro ao gerar arquivo para download")


# Função para execução direta do módulo
def main():
    """Função principal para execução direta do módulo."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Criar dados de exemplo
    df1 = pd.DataFrame({
        'data': pd.date_range(start='2020-01-01', periods=10, freq='M'),
        'valor': range(10)
    })
    
    df2 = pd.DataFrame({
        'data': pd.date_range(start='2020-01-01', periods=10, freq='M'),
        'valor': range(10, 20)
    })
    
    # Criar exportador
    exportador = Exportador()
    
    # Exportar para CSV
    link = exportador.exportar_csv(df1, "exemplo")
    logger.info(f"Link gerado: {link}")
    
    # Exportar múltiplos DataFrames
    links = exportador.exportar_multiplos_dataframes(
        {'indicador1': df1, 'indicador2': df2}
    )
    logger.info(f"Links gerados: {links}")


# Executar se for o módulo principal
if __name__ == "__main__":
    main()
