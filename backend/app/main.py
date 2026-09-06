from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from .database import Base, engine, get_db
from .models import Offer
from .schemas import OfferCreate, OfferResponse
from .services import generate_pdf, verify, generate_offer_hash


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Corporate Offer Letter API")


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Corporate Offer Letter API",
        "docs": "/docs",
    }


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ---------------------------------------------------------
# CREATE OFFER
# ---------------------------------------------------------

@app.post("/api/offers", response_model=OfferResponse)
def create(
    p: OfferCreate,
    db: Session = Depends(get_db)
):

    number = (
        "OFF-"
        + datetime.now().strftime("%Y%m%d-%H%M%S%f")[:-3]
    )

    o = Offer(
        offer_number=number,
        **p.model_dump()
    )

    db.add(o)
    db.commit()
    db.refresh(o)

    # Generate PDF + Digital Signature
    path, sig = generate_pdf(o)

    o.pdf_path = path
    o.signature = sig

    db.commit()
    db.refresh(o)

    return o


# ---------------------------------------------------------
# GET ALL OFFERS
# ---------------------------------------------------------

@app.get("/api/offers")
def all(
    db: Session = Depends(get_db)
):
    return (
        db.query(Offer)
        .order_by(Offer.id.desc())
        .all()
    )


# ---------------------------------------------------------
# DOWNLOAD PDF
# ---------------------------------------------------------

@app.get("/api/offers/{number}/pdf")
def pdf(
    number: str,
    db: Session = Depends(get_db)
):

    o = (
        db.query(Offer)
        .filter_by(offer_number=number)
        .first()
    )

    if not o:
        raise HTTPException(
            status_code=404,
            detail="Offer not found"
        )

    return FileResponse(
        o.pdf_path,
        media_type="application/pdf",
        filename=number + ".pdf"
    )


# ---------------------------------------------------------
# VERIFY OFFER
# ---------------------------------------------------------

@app.get("/api/offers/verify/{number}")
def verification(
    number: str,
    db: Session = Depends(get_db)
):

    o = (
        db.query(Offer)
        .filter_by(offer_number=number)
        .first()
    )

    if not o:
        return {
            "valid": False,
            "message": "Offer not found"
        }

    # IMPORTANT:
    # Use exactly the same canonical data that was signed
    data = generate_offer_hash(o)

    valid = verify(
        data,
        o.signature or ""
    )

    return {
        "valid": valid,
        "offer_number": number,
        "candidate_name": o.candidate_name,
        "designation": o.designation,
        "joining_date": o.joining_date,
        "status": o.status
    }