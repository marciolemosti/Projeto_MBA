# Guia de Execução - Termômetro da Economia Brasileira

## Execução Rápida

### Linux/Mac
```bash
# No diretório do projeto
./executar_dashboard.sh
```

### Windows
```cmd
# No diretório do projeto
executar_dashboard.bat
```

## Execução Manual

```bash
# 1. Navegue para o diretório do projeto
cd Projeto_MBA_v2

# 2. Instale as dependências (primeira vez apenas)
pip install -r requirements.txt

# 3. Execute o dashboard
streamlit run src/visualizacao/dashboard.py
```

## Acesso ao Dashboard

Após a execução, o dashboard estará disponível em:
- **URL Local**: http://localhost:8501
- **URL Rede**: http://0.0.0.0:8501

## Requisitos

- Python 3.8 ou superior
- Pip (gerenciador de pacotes Python)
- Conexão com internet (para dados em tempo real)

## Solução de Problemas

### "No module named 'streamlit'"
```bash
pip install streamlit
```

### "No module named 'prophet'"
```bash
pip install prophet
# ou
conda install prophet
```

### Porta 8501 em uso
```bash
streamlit run src/visualizacao/dashboard.py --server.port 8502
```

### "No module named 'dados'"
```bash
# Certifique-se de executar a partir do diretório raiz do projeto
cd Projeto_MBA_v2
streamlit run src/visualizacao/dashboard.py
```

## Funcionalidades Disponíveis

- ✅ Visualização de 7 indicadores econômicos
- ✅ Projeções com Prophet (se instalado)
- ✅ Sistema de cache para performance
- ✅ Configurações personalizáveis
- ✅ Exportação de dados
- ✅ Interface responsiva

## Desenvolvido por

**Márcio Lemos**  
Projeto MBA - Termômetro da Economia Brasileira

