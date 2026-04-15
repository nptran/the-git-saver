@echo off
venv\Scripts\activate
pip install pyinstaller colorama
pyinstaller --onefile git_feature_flow.py
pause
