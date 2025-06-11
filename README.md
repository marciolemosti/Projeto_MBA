# Termômetro da Economia Brasileira - Versão Lite

## Sobre o Projeto

Dashboard interativo simplificado para visualização e análise de indicadores econômicos brasileiros. Esta versão foi otimizada para carregamento rápido e facilidade de uso.

## Funcionalidades

- **Visualização de Indicadores**: Gráficos interativos para 7 indicadores econômicos
- **Análise Temporal**: Visualização de séries históricas e tendências
- **Cache Simples**: Sistema de cache otimizado para performance
- **Interface Responsiva**: Adaptável a diferentes dispositivos
- **Configuração Simplificada**: Configurações essenciais via YAML

## Requisitos Mínimos

- Python 3.8 ou superior
- Streamlit 1.28.0 ou superior
- Pandas 2.0.0 ou superior
- Plotly 5.15.0 ou superior

## Instalação Rápida

```bash
# Extrair o projeto
tar -xzf Projeto_MBA_Lite.tar.gz
cd Projeto_MBA_Lite

# Instalar dependências essenciais
pip install -r requirements.txt
```

## Execução

### Método 1: Scripts de Execução (Recomendado)

**Linux/Mac:**
```bash
./executar_dashboard.sh
```

**Windows:**
```cmd
executar_dashboard.bat
```

### Método 2: Execução Direta

```bash
streamlit run src/visualizacao/dashboard.py
```

## Estrutura Simplificada

```
Projeto_MBA_Lite/
├── config/                  # Configurações essenciais
│   └── dashboard_config.yaml
├── data/                    # Dados econômicos
│   ├── ipca.json
│   ├── selic.json
│   └── ...
├── src/                     # Código-fonte
│   ├── dados/               # Módulos de dados
│   ├── utils/               # Utilitários essenciais
│   └── visualizacao/        # Interface do usuário
├── executar_dashboard.sh    # Script de execução (Linux/Mac)
├── executar_dashboard.bat   # Script de execução (Windows)
└── requirements.txt         # Dependências mínimas
```

## Indicadores Disponíveis

- **IPCA**: Índice de Preços ao Consumidor Amplo
- **Taxa Selic**: Taxa básica de juros da economia
- **Câmbio USD/BRL**: Taxa de câmbio Dólar/Real
- **Déficit Primário**: Resultado primário do governo
- **Arrecadação IOF**: Imposto sobre Operações Financeiras
- **PIB (Amostra)**: Produto Interno Bruto - variação trimestral
- **Desemprego (Amostra)**: Taxa de desocupação

## Fontes de Dados

- **IPCA, PIB, Desemprego**: IBGE (Instituto Brasileiro de Geografia e Estatística)
- **Taxa Selic, Câmbio**: BCB (Banco Central do Brasil)
- **Déficit Primário**: Tesouro Nacional / BCB
- **Arrecadação IOF**: Receita Federal / BCB

## Otimizações da Versão Lite

- ✅ **Carregamento mais rápido**: Remoção de módulos desnecessários
- ✅ **Menor tamanho**: Sem testes automatizados
- ✅ **Cache simplificado**: Sistema de cache leve e eficiente
- ✅ **Dependências mínimas**: Apenas bibliotecas essenciais
- ✅ **Configuração simplificada**: YAML enxuto e focado

## Solução de Problemas

### "No module named 'dados'"
Execute sempre a partir do diretório raiz do projeto ou use os scripts fornecidos.

### "No module named 'streamlit'"
```bash
pip install streamlit
```

### Porta 8501 em uso
```bash
streamlit run src/visualizacao/dashboard.py --server.port 8502
```

## Desenvolvido por

**Márcio Lemos**  
Projeto MBA - Termômetro da Economia Brasileira  
Versão: 2.0 Lite

