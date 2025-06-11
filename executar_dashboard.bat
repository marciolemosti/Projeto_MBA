@echo off
REM Script Universal para Dashboard Econômico - Windows
REM Funciona de qualquer diretório

echo 🚀 Dashboard Econômico - Termômetro da Economia Brasileira
echo Desenvolvido por: Márcio Lemos
echo.

REM Encontrar diretório do projeto
set "PROJECT_DIR=%CD%"
:find_project
if exist "%PROJECT_DIR%\src" goto found_project
if exist "%PROJECT_DIR%\data" goto found_project
for %%i in ("%PROJECT_DIR%") do set "PARENT_DIR=%%~dpi"
if "%PARENT_DIR%" == "%PROJECT_DIR%\" goto project_not_found
set "PROJECT_DIR=%PARENT_DIR:~0,-1%"
goto find_project

:project_not_found
set "PROJECT_DIR=%CD%"

:found_project
echo 📁 Diretório do projeto: %PROJECT_DIR%

REM Verificar se o Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Erro: Python não está instalado
    pause
    exit /b 1
)

REM Verificar se o Streamlit está instalado
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Streamlit não encontrado. Tentando instalar...
    pip install streamlit pandas plotly
)

echo ✅ Verificações concluídas
echo.

REM Procurar pelo arquivo dashboard
set "DASHBOARD_FILE="

REM Opção 1: dashboard_corrigido.py (versão universal)
if exist "%PROJECT_DIR%\dashboard_corrigido.py" (
    set "DASHBOARD_FILE=%PROJECT_DIR%\dashboard_corrigido.py"
    goto run_dashboard
)

REM Opção 2: src\visualizacao\dashboard.py (versão original)
if exist "%PROJECT_DIR%\src\visualizacao\dashboard.py" (
    set "DASHBOARD_FILE=%PROJECT_DIR%\src\visualizacao\dashboard.py"
    goto run_dashboard
)

REM Opção 3: procurar em subdiretórios
for /r "%PROJECT_DIR%" %%f in (dashboard.py) do (
    set "DASHBOARD_FILE=%%f"
    goto run_dashboard
)

echo ❌ Erro: Arquivo dashboard.py não encontrado
echo    Certifique-se de estar no diretório correto do projeto
pause
exit /b 1

:run_dashboard
echo 📄 Usando dashboard: %DASHBOARD_FILE%
echo.
echo 🌐 Iniciando servidor Streamlit...
echo    URL: http://localhost:8501
echo    Para parar: Ctrl+C
echo.

REM Executar o dashboard
cd /d "%PROJECT_DIR%"
python -m streamlit run "%DASHBOARD_FILE%" --server.port 8501 --server.address 0.0.0.0

pause

