@echo off
setlocal

rem Inicia o app do operador em um dispositivo Android/iOS, emulador ou Chrome.
rem Todos os caminhos sao relativos a este arquivo.

cd /d "%~dp0mobile"
if errorlevel 1 goto :erro_pasta

where flutter >nul 2>&1
if errorlevel 1 goto :sem_flutter

if not exist ".dart_tool\" (
  echo.
  echo Primeira execucao: baixando dependencias do app mobile...
  echo.
  call flutter pub get
  if errorlevel 1 goto :erro_dependencias
)

echo.
echo ================================================
echo   Motiva Field - app mobile
echo.
echo   Conecte um celular ou inicie um emulador.
echo   O Flutter mostrara as opcoes de dispositivo.
echo ================================================
echo.

call flutter run
goto :fim

:sem_flutter
echo.
echo Flutter SDK nao encontrado no PATH.
echo Instale em https://docs.flutter.dev/get-started/install/windows
echo Depois, abra um terminal novo e execute este arquivo novamente.
goto :fim

:erro_pasta
echo.
echo Nao encontrei a pasta mobile/ ao lado deste arquivo.
goto :fim

:erro_dependencias
echo.
echo Falha ao baixar as dependencias do app mobile.
goto :fim

:fim
echo.
pause
endlocal
