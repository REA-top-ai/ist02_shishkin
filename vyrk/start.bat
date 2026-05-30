@echo off
setlocal

cd /d "%~dp0"

set "PYTHON=python"
where python >nul 2>nul
if errorlevel 1 (
    where py >nul 2>nul
    if errorlevel 1 (
        echo Python is not installed or is not available in PATH.
        echo Install Python 3.10+ and run this file again.
        pause
        exit /b 1
    )
    set "PYTHON=py -3"
)

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo Created .env from .env.example.
    )
)

set "OMDB_KEY="
if exist ".env" (
    for /f "tokens=1,* delims==" %%A in ('findstr /b "OMDB_API_KEY=" ".env" 2^>nul') do set "OMDB_KEY=%%B"
)

if "%OMDB_KEY%"=="" goto need_omdb_key
if /i "%OMDB_KEY%"=="your-omdb-key" goto need_omdb_key
goto omdb_key_ready

:need_omdb_key
echo.
echo OMDb API key is required for this project.
echo Get a free key here:
echo https://www.omdbapi.com/apikey.aspx
echo.
start "" "https://www.omdbapi.com/apikey.aspx"
set /p OMDB_KEY=Paste OMDb API key here and press Enter: 
if "%OMDB_KEY%"=="" (
    echo OMDb API key was not entered. Project was not started.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p='.env'; $key=$env:OMDB_KEY; if (!(Test-Path $p)) { Copy-Item '.env.example' $p }; $lines=Get-Content $p; $found=$false; $out=foreach($line in $lines){ if($line -like 'OMDB_API_KEY=*'){ $found=$true; 'OMDB_API_KEY=' + $key } else { $line } }; if(!$found){ $out += 'OMDB_API_KEY=' + $key }; Set-Content -Path $p -Value $out -Encoding UTF8"
echo OMDb API key saved to .env.
echo.

:omdb_key_ready

%PYTHON% -c "import flask, authlib, requests, dotenv" >nul 2>nul
if errorlevel 1 (
    echo Installing project dependencies...
    %PYTHON% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo Starting Movie Desk...
echo Open this URL if the browser does not open automatically:
echo http://127.0.0.1:5000
echo.

start "" "http://127.0.0.1:5000"
%PYTHON% app.py

pause
