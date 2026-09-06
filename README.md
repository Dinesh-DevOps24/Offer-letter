# Corporate Offer Letter Generator v3

Professional HR dashboard + corporate two-page offer letter PDF.

## Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## Frontend
Open another terminal:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173
