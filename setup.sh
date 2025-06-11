#!/bin/bash

# Script de instalação e configuração do Projeto Final MBA
# Termômetro da Economia Brasileira

echo "=========================================="
echo "PROJETO FINAL MBA - SETUP"
echo "Termômetro da Economia Brasileira"
echo "Desenvolvido por: Márcio Lemos"
echo "=========================================="

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale Python 3.8 ou superior."
    exit 1
fi

# Verificar versão do Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION encontrado"

# Verificar se pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Por favor, instale pip."
    exit 1
fi

echo "✓ pip3 encontrado"

# Criar ambiente virtual (opcional)
read -p "Deseja criar um ambiente virtual? (y/n): " create_venv
if [[ $create_venv == "y" || $create_venv == "Y" ]]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
    
    echo "📦 Ativando ambiente virtual..."
    source venv/bin/activate
    
    echo "✓ Ambiente virtual criado e ativado"
fi

# Atualizar pip
echo "📦 Atualizando pip..."
pip3 install --upgrade pip

# Instalar dependências
echo "📦 Instalando dependências..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependências instaladas com sucesso"
else
    echo "❌ Erro ao instalar dependências"
    exit 1
fi

# Criar diretórios necessários
echo "📁 Criando diretórios necessários..."
mkdir -p cache
mkdir -p logs
mkdir -p exports

echo "✓ Diretórios criados"

# Verificar estrutura do projeto
echo "🔍 Verificando estrutura do projeto..."

required_dirs=("src" "data" "config" "tests")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✓ Diretório $dir encontrado"
    else
        echo "❌ Diretório $dir não encontrado"
    fi
done

required_files=("src/visualizacao/dashboard.py" "config/dashboard_config.yaml" "data/ipca.json")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ Arquivo $file encontrado"
    else
        echo "❌ Arquivo $file não encontrado"
    fi
done

# Executar testes
echo "🧪 Executando testes..."
cd tests
python3 run_tests.py cache

if [ $? -eq 0 ]; then
    echo "✓ Testes básicos passaram"
else
    echo "⚠️  Alguns testes falharam, mas o projeto pode funcionar"
fi

cd ..

# Verificar se Streamlit funciona
echo "🚀 Verificando instalação do Streamlit..."
python3 -c "import streamlit; print('✓ Streamlit OK')"

if [ $? -eq 0 ]; then
    echo "✓ Streamlit instalado corretamente"
else
    echo "❌ Problema com instalação do Streamlit"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
echo "=========================================="
echo ""
echo "Para executar o dashboard:"
echo "  streamlit run src/visualizacao/dashboard.py"
echo ""
echo "Para executar testes:"
echo "  python tests/run_tests.py"
echo ""
echo "Para mais informações, consulte o README.md"
echo ""

# Perguntar se deseja executar o dashboard
read -p "Deseja executar o dashboard agora? (y/n): " run_dashboard
if [[ $run_dashboard == "y" || $run_dashboard == "Y" ]]; then
    echo "🚀 Iniciando dashboard..."
    streamlit run src/visualizacao/dashboard.py
fi

