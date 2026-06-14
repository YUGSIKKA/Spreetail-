# Shared Expenses Web App

A robust full-stack application to track, import, and simplify shared expenses.

## Local Setup

1. **Clone the repository**
2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. **Database Setup**:
   - Ensure you have PostgreSQL installed or adjust `.env` to use SQLite.
   - Run Alembic migrations: `alembic upgrade head`
   - Seed the database: `python seed.py`
4. **Run Backend**:
   - `uvicorn app.main:app --reload`
5. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Deployed URLs
- **Backend (Render)**: (Pending Deployment)
- **Frontend (Vercel)**: (Pending Deployment)

## AI Tools Used
- Gemini 3.1 Pro (High)
