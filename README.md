Corporate Offer Letter Generation System

A professional full-stack Corporate Offer Letter Generation System built with FastAPI, React, SQLite, ReportLab, QR Code verification, and RSA digital signatures.

The system allows HR teams to create professional offer letters, generate PDF documents, digitally sign them, and verify their authenticity using a unique verification endpoint and QR code.

🚀 Features

Professional corporate offer letter generation

Candidate and employment information management

Automatic offer number generation

CTC / salary breakup

Professional 2-page PDF offer letter

QR code based offer verification

RSA digital signature

SHA-256 based canonical offer data

Digital signature verification API

SQLite database

RESTful FastAPI backend

React frontend

CORS enabled frontend/backend communication

Offer history/listing

PDF download endpoint

API documentation with Swagger UI

🏗️ Architecture

                    ┌─────────────────────┐
                    │     React Frontend  │
                    │      Port: 5173     │
                    └──────────┬──────────┘
                               │
                               │ REST API
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Backend   │
                    │      Port: 8000     │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
            ┌────────┐   ┌──────────┐  ┌─────────────┐
            │ SQLite │   │ ReportLab│  │ RSA Signing │
            │   DB   │   │   PDF    │  │ Verification│
            └────────┘   └──────────┘  └─────────────┘
                               │
                               ▼
                         ┌──────────┐
                         │ QR Code  │
                         │ Verify   │
                         └──────────┘

🛠️ Technology Stack

Backend

Python

FastAPI

SQLAlchemy

SQLite

Pydantic

ReportLab

Cryptography

QRCode

Pillow

Uvicorn

Frontend

React

JavaScript

HTML5

CSS3

Vite

Security

RSA public/private key pair

SHA-256 hashing

RSA-PSS digital signatures

Digital signature verification

QR-based verification endpoint

📁 Project Structure

Offer-letter/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   └── services.py
│   │
│   ├── requirements.txt
│   └── offers.db
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   └── package-lock.json
│
├── generated_letters/
├── keys/
│
├── README.md
└── .gitignore

keys/, generated files, databases, virtual environments, and other sensitive/generated files are excluded from Git using .gitignore.

⚙️ Installation

1. Clone Repository

git clone https://github.com/Dinesh-DevOps24/Offer-letter.git
cd Offer-letter

2. Backend Setup

cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

3. Start Backend

From the backend directory:

python -m uvicorn app.main:app --reload

Backend:

http://127.0.0.1:8000

Health check:

http://127.0.0.1:8000/health

Swagger API documentation:

http://127.0.0.1:8000/docs

🎨 Frontend Setup

Open another terminal:

cd /home/Alex/Workshop/project1/python/Offer-letter/frontend
npm install
npm run dev

Frontend:

http://localhost:5173

🔐 Digital Signature Workflow

The system uses RSA digital signatures to protect the integrity of offer information.

Candidate Data
      │
      ▼
Canonical Offer Data
      │
      ▼
SHA-256
      │
      ▼
RSA-PSS Digital Signature
      │
      ▼
Signature stored with Offer

During verification:

Offer Data
    │
    ▼
Canonical Data
    │
    ▼
RSA Public Key
    │
    ▼
Signature Verification
    │
    ▼
Valid / Invalid

📱 QR Code Verification

Every generated offer letter contains a QR code.

The QR code points to:

/api/offers/verify/{offer_number}

Example:

http://127.0.0.1:8000/api/offers/verify/OFFER_NUMBER

The API returns verification information including whether the digital signature is valid.

🔌 API Endpoints

Method

Endpoint

Description

GET

/

API information

GET

/health

Health check

POST

/api/offers

Create new offer

GET

/api/offers

Get all offers

GET

/api/offers/{number}/pdf

Download offer PDF

GET

/api/offers/verify/{number}

Verify offer

📄 Offer Letter Generation

Candidate Details
       │
       ▼
Database Record
       │
       ▼
Offer Number Generated
       │
       ▼
Salary / CTC Calculation
       │
       ▼
PDF Generation
       │
       ▼
Digital Signature
       │
       ▼
QR Code
       │
       ▼
Final Corporate Offer Letter

🧪 Testing

Check backend health:

curl http://127.0.0.1:8000/health

Expected:

{
  "status": "ok"
}

Get all offers:

curl http://127.0.0.1:8000/api/offers

Verify an offer:

curl http://127.0.0.1:8000/api/offers/verify/OFFER_NUMBER

🔒 Security Notes

Private RSA keys must never be committed to GitHub.

The following are ignored by Git:

keys/
*.db
*.pdf
*.png
venv/
backend/venv/
.env

Never commit:

Private keys

Passwords

API keys

Database credentials

.env files

Production secrets

🌱 Git Workflow

git checkout -b feature/new-feature
git status
git add .
git commit -m "Add new feature"
git push -u origin feature/new-feature

📌 Future Improvements

User authentication and role-based access

HR/Admin dashboard

Email offer letters directly to candidates

Offer acceptance/rejection workflow

Candidate portal

Cloud database

Cloud PDF storage

Production HTTPS QR verification

Audit logs

Digital certificate management

Docker deployment

CI/CD pipeline

Automated testing

Production deployment

👨‍💻 Author

Dinesh-DevOps24

GitHub: https://github.com/Dinesh-DevOps24

📜 License

This project is intended for educational and development purposes.
