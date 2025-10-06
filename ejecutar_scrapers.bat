@echo off
echo ========================================
echo     AI News Agent - Ejecutor de Scrapers
echo ========================================
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

echo [INFO] Activando entorno virtual...
call .venv\Scripts\activate.bat

echo [INFO] Verificando que el entorno virtual esté activo...
where python
echo.

echo [INFO] Iniciando ejecución de scrapers...
echo.

echo ----------------------------------------
echo 1/3 - Ejecutando News Scraper...
echo ----------------------------------------
uv run scraper\news_scraper.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Error en news_scraper.py
    pause
    exit /b %ERRORLEVEL%
)
echo [SUCCESS] News scraper completado.
echo.

echo ----------------------------------------
echo 2/3 - Ejecutando ArXiv Scraper...
echo ----------------------------------------
uv run scraper\arxiv_scraper.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Error en arxiv_scraper.py
    pause
    exit /b %ERRORLEVEL%
)
echo [SUCCESS] ArXiv scraper completado.
echo.

echo ----------------------------------------
echo 3/3 - Ejecutando YouTube Scraper...
echo ----------------------------------------
uv run scraper\youtube_scraper.py
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Error en youtube_scraper.py
    pause
    exit /b %ERRORLEVEL%
)
echo [SUCCESS] YouTube scraper completado.
echo.

echo ========================================
echo   TODOS LOS SCRAPERS COMPLETADOS
echo ========================================
echo.
echo Los datos han sido actualizados en la base de datos.
echo Puedes cerrar esta ventana o presionar cualquier tecla para salir.
echo.

pause