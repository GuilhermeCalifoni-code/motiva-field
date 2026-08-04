@echo off
setlocal

rem Sobe o painel web em modo desenvolvimento e abre o navegador.
rem Usa o diretorio do proprio script (%~dp0), entao roda em qualquer maquina
rem que tenha o repositorio clonado - sem caminho absoluto embutido.

cd /d "%~dp0web"
if errorlevel 1 goto :erro

where npm >nul 2>&1
if errorlevel 1 goto :sem_node

if not exist "node_modules\" (
  echo.
  echo Primeira execucao: instalando dependencias, isso leva um minuto...
  echo.
  call npm install
  if errorlevel 1 goto :erro
)

echo.
echo Motiva Field - painel web
echo Subindo em http://localhost:5173
echo Para parar: feche esta janela ou pressione Ctrl+C.
echo.

call npm run dev -- --open
goto :fim

:sem_node
echo.
echo Node.js nao encontrado no PATH.
echo Instale em https://nodejs.org e abra um terminal novo.
echo.
pause
exit /b 1

:erro
echo.
echo Falha ao iniciar o painel. Confira a mensagem acima.
echo.
pause
exit /b 1

:fim
endlocal
