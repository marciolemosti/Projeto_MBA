#!/bin/bash

# Script Universal para Dashboard Econômico
# Funciona de qualquer diretório

echo "🚀 Dashboard Econômico - Termômetro da Economia Brasileira"
echo "Desenvolvido por: Márcio Lemos"
echo ""

# Função para encontrar o diretório do projeto
find_project_dir() {
    local current_dir="$PWD"
    
    # Procurar pelo diretório que contém 'src' ou 'data'
    while [ "$current_dir" != "/" ]; do
        if [ -d "$current_dir/src" ] || [ -d "$current_dir/data" ]; then
            echo "$current_dir"
            return 0
        fi
        current_dir=$(dirname "$current_dir")
    done
    
    # Se não encontrou, assumir diretório atual
    echo "$PWD"
}

# Encontrar diretório do projeto
PROJECT_DIR=$(find_project_dir)
echo "📁 Diretório do projeto: $PROJECT_DIR"

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: Python 3 não está instalado"
    exit 1
fi

# Verificar se o Streamlit está instalado
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "⚠️  Streamlit não encontrado. Tentando instalar..."
    pip3 install streamlit pandas plotly
fi

echo "✅ Verificações concluídas"
echo ""

# Procurar pelo arquivo dashboard
DASHBOARD_FILE=""

# Opção 1: dashboard_corrigido.py (versão universal)
if [ -f "$PROJECT_DIR/dashboard_corrigido.py" ]; then
    DASHBOARD_FILE="$PROJECT_DIR/dashboard_corrigido.py"
# Opção 2: src/visualizacao/dashboard.py (versão original)
elif [ -f "$PROJECT_DIR/src/visualizacao/dashboard.py" ]; then
    DASHBOARD_FILE="$PROJECT_DIR/src/visualizacao/dashboard.py"
# Opção 3: procurar em subdiretórios
else
    DASHBOARD_FILE=$(find "$PROJECT_DIR" -name "dashboard.py" -type f | head -1)
fi

if [ -z "$DASHBOARD_FILE" ]; then
    echo "❌ Erro: Arquivo dashboard.py não encontrado"
    echo "   Certifique-se de estar no diretório correto do projeto"
    exit 1
fi

echo "📄 Usando dashboard: $DASHBOARD_FILE"
echo ""
echo "🌐 Iniciando servidor Streamlit..."
echo "   URL: http://localhost:8501"
echo "   Para parar: Ctrl+C"
echo ""

# Executar o dashboard
cd "$PROJECT_DIR"
python3 -m streamlit run "$DASHBOARD_FILE" --server.port 8501 --server.address 0.0.0.0

