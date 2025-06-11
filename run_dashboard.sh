#!/bin/bash

# Script para executar o Dashboard Econômico
# Desenvolvido por: Márcio Lemos

echo "🚀 Iniciando Dashboard Econômico - Termômetro da Economia Brasileira"
echo "Desenvolvido por: Márcio Lemos"
echo ""

# Verificar se está no diretório correto
if [ ! -f "src/visualizacao/dashboard.py" ]; then
    echo "❌ Erro: Execute este script a partir do diretório raiz do projeto"
    echo "   Certifique-se de estar em: Projeto_Final_MBA/"
    exit 1
fi

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: Python 3 não está instalado"
    exit 1
fi

# Verificar se o Streamlit está instalado
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "⚠️  Streamlit não encontrado. Instalando dependências..."
    pip3 install -r requirements.txt
fi

echo "✅ Verificações concluídas"
echo ""
echo "🌐 Iniciando servidor Streamlit..."
echo "   URL: http://localhost:8501"
echo "   Para parar: Ctrl+C"
echo ""

# Executar o dashboard
cd src/visualizacao
python3 -m streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0

