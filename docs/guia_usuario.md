# Documentação do Dashboard de Indicadores Socioeconômicos Brasileiros

## Visão Geral

O Dashboard de Indicadores Socioeconômicos Brasileiros é uma aplicação interativa desenvolvida em Streamlit que permite visualizar, analisar e prever indicadores econômicos do Brasil. A aplicação integra dados de diversas fontes oficiais, como Banco Central do Brasil (BCB) e Instituto Brasileiro de Geografia e Estatística (IBGE), oferecendo uma visão abrangente da economia brasileira.

## Funcionalidades Principais

### 1. Visualização de Indicadores
- **Indicadores disponíveis**: PIB, Taxa de Desemprego, Déficit Primário, Arrecadação de IOF, IPCA, Câmbio e Taxa Selic
- **Métricas-chave**: Valores atuais, variações e estatísticas básicas
- **Gráficos interativos**: Visualização histórica com detalhamento ao passar o mouse

### 2. Análise Detalhada
- **Estatísticas detalhadas** por indicador
- **Médias móveis** para identificação de tendências
- **Detecção automática de eventos significativos** (picos, vales, mudanças abruptas)

### 3. Comparação entre Indicadores
- **Correlação** entre diferentes indicadores
- **Visualização comparativa** de múltiplos indicadores
- **Normalização** para comparar indicadores com diferentes escalas

### 4. Projeções Futuras
- **Previsão para 2 anos** utilizando o algoritmo Prophet
- **Intervalos de confiança** para avaliar a incerteza das previsões
- **Análise de tendências** projetadas

### 5. Exportação de Dados
- **Exportação em CSV** de dados históricos e previsões
- **Opções de exportação** individual ou em conjunto
- **Formatação adequada** para uso em outras ferramentas

## Requisitos do Sistema

- Python 3.8 ou superior
- Bibliotecas: streamlit, pandas, numpy, plotly, prophet, requests
- Acesso à internet para atualização de dados

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/marciolemosti/Projeto_MBA.git
cd Projeto_MBA
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Execute a aplicação:
```bash
streamlit run src/visualizacao/dashboard.py
```

## Estrutura do Projeto

```
termometro-economia/
├── data/                      # Diretório para armazenamento de dados
├── src/                       # Código-fonte da aplicação
│   ├── dados/                 # Módulos de extração e processamento de dados
│   │   ├── extratores/        # Extratores de dados de fontes externas
│   │   │   ├── bcb.py         # Extrator de dados do Banco Central
│   │   │   └── ibge.py        # Extrator de dados do IBGE
│   │   └── processadores/     # Processadores de dados
│   │       ├── eventos.py     # Detector de eventos significativos
│   │       └── previsao.py    # Previsor de séries temporais
│   ├── utils/                 # Utilitários
│   │   ├── configuracao.py    # Configurações centralizadas
│   │   └── logger.py          # Configuração de logging
│   └── visualizacao/          # Componentes de visualização
│       ├── componentes/       # Componentes reutilizáveis
│       │   ├── exibidores.py  # Componentes para exibição de dados
│       │   └── exportadores.py # Componentes para exportação de dados
│       └── dashboard.py       # Aplicação principal do dashboard
├── assets/                    # Recursos estáticos (ícones, imagens)
├── .github/                   # Configurações do GitHub
│   └── workflows/             # Workflows do GitHub Actions
│       └── atualizacao_dados.yml # Workflow para atualização automática de dados
├── docker-compose.yml         # Configuração do Docker Compose
├── Dockerfile                 # Configuração do Docker
├── requirements.txt           # Dependências do projeto
└── README.md                  # Documentação principal
```

## Guia de Uso

### Navegação Básica

O dashboard está organizado em cinco abas principais:

1. **Visão Geral**: Apresenta métricas-chave e visualização histórica dos indicadores selecionados.
2. **Detalhes**: Fornece análise detalhada de um indicador específico, incluindo estatísticas e eventos significativos.
3. **Comparativo**: Permite comparar diferentes indicadores e analisar correlações.
4. **Previsões**: Exibe projeções futuras para os indicadores selecionados.
5. **Exportar Dados**: Oferece opções para exportação de dados em formato CSV.

### Filtros e Configurações

No painel lateral, você encontrará:

- **Botão de Atualização de Dados**: Busca dados atualizados das fontes oficiais.
- **Filtro de Período**: Permite selecionar o intervalo de anos para análise.
- **Seleção de Indicadores**: Escolha quais indicadores deseja visualizar.
- **Opções de Visualização**: Configure projeções, eventos significativos e normalização.

### Atualização de Dados

Os dados são atualizados automaticamente diariamente através do GitHub Actions. Para atualização manual:

1. Clique no botão "🔄 Atualizar Dados" no painel lateral.
2. Aguarde a conclusão do processo de atualização.
3. Os novos dados serão carregados automaticamente nas visualizações.

### Visualização de Projeções

Para visualizar projeções futuras:

1. Ative a opção "Mostrar projeções" no painel lateral.
2. Ajuste o horizonte de projeção conforme necessário (padrão: 2 anos).
3. Navegue até a aba "Previsões" para uma análise detalhada.
4. Passe o mouse sobre o gráfico para ver valores específicos.

### Exportação de Dados

Para exportar dados:

1. Navegue até a aba "Exportar Dados".
2. Selecione o tipo de conteúdo (dados históricos, previsões ou ambos).
3. Clique no botão de download para o indicador desejado ou para todos os indicadores.
4. Os dados serão baixados em formato CSV, pronto para uso em outras ferramentas.

## Indicadores Disponíveis

### PIB (Produto Interno Bruto)
- **Fonte**: IBGE
- **Periodicidade**: Trimestral
- **Unidade**: R$ bilhões
- **Descrição**: Soma de todos os bens e serviços finais produzidos no país.

### Taxa de Desemprego
- **Fonte**: IBGE (PNAD Contínua)
- **Periodicidade**: Trimestral
- **Unidade**: Percentual (%)
- **Descrição**: Percentual da população economicamente ativa que está desempregada.

### Déficit Primário
- **Fonte**: Tesouro Nacional/BCB
- **Periodicidade**: Mensal
- **Unidade**: R$ milhões
- **Descrição**: Resultado das contas do governo antes do pagamento de juros.

### Arrecadação de IOF
- **Fonte**: Receita Federal/BCB
- **Periodicidade**: Mensal
- **Unidade**: R$ milhões
- **Descrição**: Arrecadação do Imposto sobre Operações Financeiras.

### IPCA (Índice Nacional de Preços ao Consumidor Amplo)
- **Fonte**: IBGE/BCB
- **Periodicidade**: Mensal
- **Unidade**: Percentual ao mês (% a.m.)
- **Descrição**: Principal índice de inflação do Brasil.

### Câmbio (USD/BRL)
- **Fonte**: BCB
- **Periodicidade**: Diária (consolidada mensalmente)
- **Unidade**: R$
- **Descrição**: Taxa de câmbio do dólar americano (venda).

### Taxa Selic
- **Fonte**: BCB
- **Periodicidade**: Diária (consolidada mensalmente)
- **Unidade**: Percentual ao ano (% a.a.)
- **Descrição**: Taxa básica de juros da economia brasileira.

## Metodologia de Previsão

O dashboard utiliza o algoritmo Prophet, desenvolvido pelo Facebook, para gerar previsões dos indicadores econômicos. Principais características:

- **Modelo aditivo**: Combina tendência, sazonalidade e efeitos de feriados.
- **Robustez**: Lida bem com dados faltantes e outliers.
- **Sazonalidade**: Captura padrões sazonais em diferentes escalas (anual, mensal, semanal).
- **Intervalos de confiança**: Fornece estimativas de incerteza para as previsões.

### Limitações das Previsões

- As previsões são baseadas em padrões históricos e podem não capturar eventos imprevisíveis.
- A precisão diminui à medida que o horizonte de previsão aumenta.
- Mudanças estruturais na economia podem afetar a qualidade das previsões.

## Detecção de Eventos Significativos

O dashboard identifica automaticamente eventos significativos nos indicadores econômicos:

- **Picos e vales**: Valores extremos que se destacam na série temporal.
- **Mudanças abruptas**: Variações percentuais significativas entre períodos consecutivos.
- **Inversões de tendência**: Mudanças na direção da tendência de longo prazo.

## Automação com GitHub Actions

O projeto inclui um workflow do GitHub Actions que:

1. Executa diariamente à meia-noite (UTC).
2. Extrai dados atualizados das fontes oficiais.
3. Processa os dados e gera previsões.
4. Salva os resultados no repositório.

Para configurar a automação em seu próprio repositório:

1. Faça fork do repositório.
2. Ative o GitHub Actions nas configurações do repositório.
3. Verifique se as permissões estão configuradas corretamente para permitir commits automáticos.

## Execução com Docker

Para executar o dashboard usando Docker:

1. Certifique-se de ter Docker e Docker Compose instalados.
2. Execute o comando:
```bash
docker-compose up
```
3. Acesse o dashboard em `http://localhost:8501`.

## Solução de Problemas

### Dados não aparecem no dashboard
- Verifique se os arquivos de dados existem no diretório `data/`.
- Execute manualmente os extratores para atualizar os dados:
  ```bash
  python -m src.dados.extratores.bcb
  python -m src.dados.extratores.ibge
  ```

### Erro ao gerar previsões
- Verifique se a biblioteca Prophet está instalada corretamente.
- Certifique-se de que há dados históricos suficientes para o indicador.

### Problemas com o GitHub Actions
- Verifique as permissões do repositório em Settings > Actions > General.
- Certifique-se de que a opção "Read and write permissions" está selecionada.

## UNIVERSIDADE DE FORTALEZA - UNIFOR
- Curso de MBA em Gestão analítica com BI e Big Data
- Autor: Márcio Lemos
- Orientador: Prof. Ms. Thiago Bluhm

