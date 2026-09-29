@echo off
echo Setting up Mother-Tongue Education Platform...
echo.

echo [1/5] Setting up Python virtual environment (project root: venv\)...
python -m venv venv
call venv\Scripts\activate

echo [2/5] Installing Python dependencies...
pip install -r backend\requirements.txt
echo Installing CPU-only PyTorch (smaller than CUDA build)...
pip install torch==2.4.1 --index-url https://download.pytorch.org/whl/cpu

echo [3/5] Creating .env file...
if not exist .env (
    copy backend\.env.example .env
    echo Please edit .env with your configuration
)

echo [4/5] Creating storage directories...
if not exist storage mkdir storage
if not exist storage\lectures mkdir storage\lectures
if not exist storage\dubbed mkdir storage\dubbed
if not exist storage\transcripts mkdir storage\transcripts
if not exist storage\worksheets mkdir storage\worksheets

echo [5/5] Setting up frontend...
cd ..\frontend
call npm install

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo NEXT STEPS:
echo 1. Start PostgreSQL and Redis:
echo    docker compose up -d
echo    - PostgreSQL on host port 5433 (5432 is used by a native install)
echo    - Redis on port 6379
echo.
echo 2. Update root .env with:
echo    - Database credentials
echo    - API keys (GEMINI_API_KEY = Omniroute unified key for translation)
echo.
echo 3. Initialize database:
echo    cd backend ^&^& ..\venv\Scripts\activate
echo    python -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"
echo.
echo 4. Start the services:
echo    Terminal 1: cd backend ^&^& ..\venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo    Terminal 2: cd backend ^&^& ..\venv\Scripts\activate ^&^& celery -A app.tasks worker --loglevel=info --pool=solo
echo    Terminal 3: cd frontend ^&^& npm run dev
echo.
echo Visit http://localhost:5173 to access the application
echo.
