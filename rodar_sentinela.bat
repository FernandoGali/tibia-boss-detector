@echo off
rem Roda o sentinela a partir da pasta do projeto e guarda a saida num arquivo
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
"C:\Users\ferna\AppData\Local\Programs\Python\Python313\python.exe" sentinela.py >> sentinela_saida.txt 2>&1
