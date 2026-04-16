@echo off
cd /d C:\Users\gabri\OneDrive\Documentos\applol
uvicorn app.main:app --host 127.0.0.1 --port 8011 --reload
