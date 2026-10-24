@echo off
cd /d "%~dp0"
python -m http.server 5281 --bind 127.0.0.1 --directory dist
