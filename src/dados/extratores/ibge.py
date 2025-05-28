"""
Módulo para extração de dados do IBGE (PIB e Taxa de Desemprego).

Este módulo implementa classes e funções para extrair dados do IBGE,
incluindo PIB e Taxa de Desemprego da PNAD Contínua.
"""

import os
import json
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

# Configuração de logging
logger = logging.getLogger(__name__)

class ExtratorIBGE:
    """Classe para extração de dados do IBGE."""
    
    def __init__(self, diretorio_dados: str = "data"):
        """
        Inicializa o extrator de dados do IBGE.
        
        Args:
            diretorio_dados: Diretório onde os dados serão salvos
        """
        self.diretorio_dados = diretorio_dados
        self._criar_diretorio_se_nao_existir()
        logger.info(f"ExtratorIBGE inicializado com diretório de dados: {self.diretorio_dados}")
    
    def _criar_diretorio_se_nao_existir(self) -> None:
        """Cria o diretório de dados se não existir."""
        if not os.path.exists(self.diretorio_dados):
            os.makedirs(self.diretorio_dados)
            logger.info(f"Diretório de dados criado: {self.diretorio_dados}")
    
    def extrair_pib(self) -> pd.DataFrame:
        """
        Extrai dados do PIB do IBGE.
        
        Returns:
            DataFrame com os dados do PIB
        """
        logger.info("Iniciando extração de dados do PIB do IBGE")
        
        # URL da API do SIDRA/IBGE para o PIB trimestral
        url = "https://api.sidra.ibge.gov.br/values/t/1846/n1/all/v/all/p/all/c11255/90707/d/v585%202"
        
        try:
            # Fazer requisição à API
            response = requests.get(url)
            response.raise_for_status()
            
            # Converter resposta para DataFrame
            dados = response.json()
            df = pd.DataFrame(dados[1:])  # Pular a primeira linha que contém metadados
            
            # Processar e limpar os dados
            df = self._processar_dados_pib(df)
            
            # Salvar dados
            self._salvar_dados(df, "pib.json")
            
            logger.info(f"Extração de dados do PIB concluída. Total de registros: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados do PIB: {str(e)}")
            # Tentar carregar dados salvos anteriormente
            df = self._carregar_dados_salvos("pib.json")
            if df is not None:
                logger.info(f"Usando dados salvos do PIB. Total de registros: {len(df)}")
                return df
            else:
                # Se não houver dados salvos, criar DataFrame vazio
                logger.warning("Não foi possível carregar dados salvos do PIB. Retornando DataFrame vazio.")
                return pd.DataFrame(columns=["data", "valor"])
    
    def _processar_dados_pib(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa e limpa os dados do PIB.
        
        Args:
            df: DataFrame com os dados brutos do PIB
            
        Returns:
            DataFrame processado
        """
        # Renomear colunas
        if "V" in df.columns and "D2C" in df.columns:
            df = df.rename(columns={"V": "valor", "D2C": "data"})
        
        # Converter valor para numérico
        if "valor" in df.columns:
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        
        # Converter data para datetime
        if "data" in df.columns:
            # Formato esperado: "2023 1º trimestre"
            df["data"] = df["data"].apply(self._converter_trimestre_para_data)
        
        # Remover linhas com valores nulos
        df = df.dropna(subset=["data", "valor"])
        
        # Selecionar apenas as colunas necessárias
        colunas = ["data", "valor"]
        df = df[colunas]
        
        # Ordenar por data
        df = df.sort_values("data")
        
        return df
    
    def _converter_trimestre_para_data(self, texto_trimestre: str) -> Optional[datetime]:
        """
        Converte texto de trimestre para data.
        
        Args:
            texto_trimestre: Texto no formato "2023 1º trimestre"
            
        Returns:
            Data convertida ou None se falhar
        """
        try:
            # Extrair ano e trimestre
            partes = texto_trimestre.split()
            if len(partes) >= 2:
                ano = int(partes[0])
                trimestre_texto = partes[1]
                
                # Determinar o mês com base no trimestre
                if "1º" in trimestre_texto or "1" in trimestre_texto:
                    mes = 3  # Fim do primeiro trimestre
                elif "2º" in trimestre_texto or "2" in trimestre_texto:
                    mes = 6  # Fim do segundo trimestre
                elif "3º" in trimestre_texto or "3" in trimestre_texto:
                    mes = 9  # Fim do terceiro trimestre
                elif "4º" in trimestre_texto or "4" in trimestre_texto:
                    mes = 12  # Fim do quarto trimestre
                else:
                    return None
                
                # Criar data
                return datetime(ano, mes, 1)
            
            return None
        except Exception as e:
            logger.error(f"Erro ao converter trimestre para data: {str(e)}")
            return None
    
    def extrair_desemprego(self) -> pd.DataFrame:
        """
        Extrai dados da taxa de desemprego da PNAD Contínua.
        
        Returns:
            DataFrame com os dados da taxa de desemprego
        """
        logger.info("Iniciando extração de dados da taxa de desemprego da PNAD Contínua")
        
        # URL da API do SIDRA/IBGE para a taxa de desemprego
        url = "https://api.sidra.ibge.gov.br/values/t/6381/n1/all/v/4099/p/all/d/v4099%201"
        
        try:
            # Fazer requisição à API
            response = requests.get(url)
            response.raise_for_status()
            
            # Converter resposta para DataFrame
            dados = response.json()
            df = pd.DataFrame(dados[1:])  # Pular a primeira linha que contém metadados
            
            # Processar e limpar os dados
            df = self._processar_dados_desemprego(df)
            
            # Salvar dados
            self._salvar_dados(df, "desemprego.json")
            
            logger.info(f"Extração de dados da taxa de desemprego concluída. Total de registros: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados da taxa de desemprego: {str(e)}")
            # Tentar carregar dados salvos anteriormente
            df = self._carregar_dados_salvos("desemprego.json")
            if df is not None:
                logger.info(f"Usando dados salvos da taxa de desemprego. Total de registros: {len(df)}")
                return df
            else:
                # Se não houver dados salvos, criar DataFrame vazio
                logger.warning("Não foi possível carregar dados salvos da taxa de desemprego. Retornando DataFrame vazio.")
                return pd.DataFrame(columns=["data", "valor"])
    
    def _processar_dados_desemprego(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Processa e limpa os dados da taxa de desemprego.
        
        Args:
            df: DataFrame com os dados brutos da taxa de desemprego
            
        Returns:
            DataFrame processado
        """
        # Renomear colunas
        if "V" in df.columns and "D3C" in df.columns:
            df = df.rename(columns={"V": "valor", "D3C": "data"})
        
        # Converter valor para numérico
        if "valor" in df.columns:
            df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
        
        # Converter data para datetime
        if "data" in df.columns:
            # Formato esperado: "1º trimestre 2023"
            df["data"] = df["data"].apply(self._converter_trimestre_pnad_para_data)
        
        # Remover linhas com valores nulos
        df = df.dropna(subset=["data", "valor"])
        
        # Selecionar apenas as colunas necessárias
        colunas = ["data", "valor"]
        df = df[colunas]
        
        # Ordenar por data
        df = df.sort_values("data")
        
        return df
    
    def _converter_trimestre_pnad_para_data(self, texto_trimestre: str) -> Optional[datetime]:
        """
        Converte texto de trimestre da PNAD para data.
        
        Args:
            texto_trimestre: Texto no formato "1º trimestre 2023"
            
        Returns:
            Data convertida ou None se falhar
        """
        try:
            # Extrair ano e trimestre
            partes = texto_trimestre.split()
            if len(partes) >= 2:
                ano = int(partes[-1])  # Último elemento é o ano
                trimestre_texto = partes[0]
                
                # Determinar o mês com base no trimestre
                if "1º" in trimestre_texto or "1" in trimestre_texto:
                    mes = 3  # Fim do primeiro trimestre
                elif "2º" in trimestre_texto or "2" in trimestre_texto:
                    mes = 6  # Fim do segundo trimestre
                elif "3º" in trimestre_texto or "3" in trimestre_texto:
                    mes = 9  # Fim do terceiro trimestre
                elif "4º" in trimestre_texto or "4" in trimestre_texto:
                    mes = 12  # Fim do quarto trimestre
                else:
                    return None
                
                # Criar data
                return datetime(ano, mes, 1)
            
            return None
        except Exception as e:
            logger.error(f"Erro ao converter trimestre PNAD para data: {str(e)}")
            return None
    
    def _salvar_dados(self, df: pd.DataFrame, nome_arquivo: str) -> None:
        """
        Salva os dados em um arquivo JSON.
        
        Args:
            df: DataFrame com os dados
            nome_arquivo: Nome do arquivo para salvar
        """
        try:
            # Converter datas para string no formato ISO
            df_json = df.copy()
            if "data" in df_json.columns and df_json["data"].dtype != 'object':
                df_json["data"] = df_json["data"].dt.strftime("%Y-%m-%d")
            
            # Converter para registros (lista de dicionários)
            registros = df_json.to_dict(orient="records")
            
            # Salvar como JSON
            caminho_arquivo = os.path.join(self.diretorio_dados, nome_arquivo)
            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                json.dump(registros, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Dados salvos em: {caminho_arquivo}")
        except Exception as e:
            logger.error(f"Erro ao salvar dados em {nome_arquivo}: {str(e)}")
    
    def _carregar_dados_salvos(self, nome_arquivo: str) -> Optional[pd.DataFrame]:
        """
        Carrega dados salvos anteriormente.
        
        Args:
            nome_arquivo: Nome do arquivo para carregar
            
        Returns:
            DataFrame com os dados ou None se falhar
        """
        try:
            caminho_arquivo = os.path.join(self.diretorio_dados, nome_arquivo)
            if os.path.exists(caminho_arquivo):
                with open(caminho_arquivo, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                
                df = pd.DataFrame(dados)
                
                # Converter data para datetime
                if "data" in df.columns:
                    df["data"] = pd.to_datetime(df["data"])
                
                return df
            else:
                logger.warning(f"Arquivo não encontrado: {caminho_arquivo}")
                return None
        except Exception as e:
            logger.error(f"Erro ao carregar dados de {nome_arquivo}: {str(e)}")
            return None


# Função para execução direta do módulo
def main():
    """Função principal para execução direta do módulo."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Criar extrator
    extrator = ExtratorIBGE()
    
    # Extrair dados
    df_pib = extrator.extrair_pib()
    logger.info(f"Dados do PIB extraídos: {len(df_pib)} registros")
    
    df_desemprego = extrator.extrair_desemprego()
    logger.info(f"Dados da taxa de desemprego extraídos: {len(df_desemprego)} registros")


# Executar se for o módulo principal
if __name__ == "__main__":
    main()
