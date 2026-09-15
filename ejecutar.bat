@echo off
title Orientador de Vacantes CNSC - Ciudadano
color 1F
cd /d "%~dp0"

echo ============================================================
echo ORIENTADOR DE VACANTES PUBLICAS CNSC
echo Aplicativo ciudadano - Indice de compatibilidad
echo ============================================================

set PYTHON=
py -3.11 --version >nul 2>&1
if not errorlevel 1 set PYTHON=py -3.11
if defined PYTHON goto :python_ok
py --version >nul 2>&1
if not errorlevel 1 set PYTHON=py
if defined PYTHON goto :python_ok
python --version >nul 2>&1
if not errorlevel 1 set PYTHON=python
if defined PYTHON goto :python_ok
python3 --version >nul 2>&1
if not errorlevel 1 set PYTHON=python3
if defined PYTHON goto :python_ok

echo [ERROR] Python no fue encontrado. Se recomienda Python 3.11.
pause
exit /b 1

:python_ok
echo [1/5] Verificando archivos...
for %%F in (app.py motor_inferencia.py paquete_modelo_cnsc_v1.joblib requirements.txt) do (
    if not exist "%%F" (
        echo [ERROR] Falta %%F
        pause
        exit /b 1
    )
)

echo [2/5] Preparando entorno virtual...
if not exist "venv\" %PYTHON% -m venv venv
if errorlevel 1 goto :error

echo [3/5] Instalando dependencias...
call venv\Scripts\activate.bat
venv\Scripts\python.exe -m pip install --upgrade pip -q
venv\Scripts\pip.exe install -r requirements.txt -q
if errorlevel 1 goto :error

echo [4/5] Ejecutando pruebas funcionales...
venv\Scripts\python.exe test_motor.py
if errorlevel 1 goto :error

echo [5/5] Iniciando interfaz ciudadana...
start "" "http://localhost:8501"
venv\Scripts\streamlit.exe run app.py --server.port 8501 --browser.gatherUsageStats false
goto :fin

:error
echo [ERROR] No fue posible preparar o validar el aplicativo.
pause
exit /b 1

:fin
pause
