@echo off
echo ==========================================
echo      INICIANDO BUSCADOR DIOF - RO
echo ==========================================

REM Verifica se o Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado! Instale o Python marcando a opcao "Add to PATH".
    pause
    exit /b
)

echo.
echo [1/3] Atualizando instalador (pip)...
python -m pip install --upgrade pip

echo.
echo [2/3] Instalando dependencias (modo usuario)...
REM O flag --user instala na pasta do usuario, evitando erro de permissao de administrador
python -m pip install -r requirements.txt --user

echo.
echo [3/3] Iniciando aplicacao...
echo A pagina abrira no seu navegador automaticamente.
echo.

REM Usamos "python -m streamlit" ao inves de apenas "streamlit"
REM Isso garante que o Windows encontre o programa mesmo sem estar no PATH
python -m streamlit run app.py

pause