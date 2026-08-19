@echo off
setlocal

rem Sobe a interface de teste da visao computacional e abre o navegador.
rem
rem Resolve tudo a partir do diretorio do proprio arquivo (%~dp0), sem caminho
rem absoluto embutido: funciona em qualquer maquina com o repositorio clonado.
rem
rem A janela fica aberta ao terminar ou falhar, para a mensagem de erro nao
rem sumir junto com o console.

rem Porta definida em vision/app.py, no app.run() do final do arquivo.
set "ENDERECO=http://127.0.0.1:8766/"

cd /d "%~dp0vision"
if errorlevel 1 goto :erro_pasta

where python >nul 2>&1
if errorlevel 1 goto :sem_python

if not exist ".venv\Scripts\python.exe" goto :criar_venv
goto :subir

:criar_venv
echo.
echo Primeira execucao: criando o ambiente virtual...
echo.
python -m venv .venv
if errorlevel 1 goto :erro_venv
echo Instalando dependencias. Baixa o TensorFlow, entao leva alguns minutos.
echo.
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :erro_deps
echo.
echo Ambiente pronto.

:subir
echo.
echo ================================================
echo   Motiva Visao - interface de teste
echo   %ENDERECO%
echo.
echo   Para parar: feche esta janela ou pressione Ctrl+C.
echo ================================================
echo.

rem Abridor em segundo plano: espera o Flask responder e so entao abre a
rem pagina, para o navegador nao cair em "nao foi possivel conectar".
rem
rem Delegado ao PowerShell de proposito. A tentativa de reinvocar este mesmo
rem .bat com um argumento falhava: o `start` engolia o argumento e reabria o
rem script inteiro com `cmd /K`, subindo um segundo servidor numa janela que
rem nunca fechava.
start "" /min powershell -NoProfile -ExecutionPolicy Bypass -Command "$u='%ENDERECO%'; for($i=0;$i -lt 60;$i++){ try{ $null = Invoke-WebRequest $u -UseBasicParsing -TimeoutSec 2; break } catch { Start-Sleep -Seconds 1 } }; Start-Process $u"

".venv\Scripts\python.exe" app.py
if errorlevel 1 goto :erro_app

echo.
echo Servidor encerrado.
goto :fim

:sem_python
echo.
echo Python nao encontrado no PATH.
echo Instale em https://python.org e abra um terminal novo.
goto :fim

:erro_pasta
echo.
echo Nao encontrei a pasta vision/ ao lado deste arquivo.
echo Este .bat precisa ficar na raiz da worktree, junto da pasta vision.
goto :fim

:erro_venv
echo.
echo Falha ao criar o ambiente virtual em vision\.venv.
goto :fim

:erro_deps
echo.
echo Falha ao instalar as dependencias de vision\requirements.txt.
echo Confira sua conexao e rode de novo.
goto :fim

:erro_app
echo.
echo O servidor terminou com erro. A mensagem esta logo acima.
goto :fim

:fim
echo.
pause
endlocal
