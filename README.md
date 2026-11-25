# VHERO - Backend

FastAPI backend for the VHERO app.

## Project Structure

- `controller/` - API routing (endpoints)
- `schemas/` - Request/response schemas
- `services/` - Business logic and helpers (e.g., email sending)

## Setup & Run

1. Create and activate a virtual environment

   Windows:
   python -m venv venv
   .\venv\Scripts\activate

   Linux/macOS:
   python3 -m venv venv
   source venv/bin/activate

2. Install dependencies

   pip install -r requirements.txt

3. Start the server

   uvicorn app:app --reload --host 0.0.0.0 --port 8000

The API will be available at http://localhost:8000, and the interactive docs at http://localhost:8000/docs.
