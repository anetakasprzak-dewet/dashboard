Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

if (!(Test-Path ".\.venv")) {
    python -m venv .venv
}

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install --no-index --find-links=.\wheelhouse -r .\requirements.txt

python -c "import streamlit; print('OK', streamlit.__version__)"