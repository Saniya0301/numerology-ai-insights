"""
FastAPI backend for Numerology AI Insights.
Wraps the existing numerology, RAG, and PDF services as HTTP endpoints
for the frontend to call.

IMPORTANT — memory optimization for constrained hosting (e.g. Render's
512MB free tier): the heavy AI stack (LangChain, ChromaDB, google-
generativeai, FastEmbed) is imported LAZILY, inside each endpoint
function that actually needs it, rather than at module load time.
This keeps lightweight endpoints (like /api/profile, which is pure
calculation) from ever loading those libraries into memory. AI-dependent
endpoints (/api/life-areas, /api/chat, /api/compatibility) still load
the full stack on first use — this doesn't eliminate their memory cost,
but it stops every endpoint from paying that cost regardless of need.

Run with: uvicorn api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import csv
from pathlib import Path

# Lightweight import only — no AI libraries pulled in here
from services.numerology import (
    get_full_numerology_profile,
    get_life_path_breakdown,
    calculate_pinnacles,
    calculate_challenges,
    calculate_karmic_lessons,
    calculate_compatibility,
    calculate_maturity_number,
)
from services.report_generator import generate_pdf_report

app = FastAPI(title="Numerology AI Insights API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # loosened for local development; restrict before deploying live
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NOTE: no startup event loading embeddings/ChromaDB here anymore — that
# work is deferred until an AI endpoint is actually called (see below).
# Since the pre-built knowledge_base vector store is committed to the
# repo (not gitignored), it's already present on disk at deploy time, so
# the first AI request just loads it rather than rebuilding from scratch.


# ---------- Request/response models ----------

class ProfileRequest(BaseModel):
    full_name: str
    day: int
    month: int
    year: int


class ChatRequest(BaseModel):
    full_name: str
    profile: dict
    question: str
    chat_history: list = []


class CompatibilityRequest(BaseModel):
    name_a: str
    day_a: int
    month_a: int
    year_a: int
    name_b: str
    day_b: int
    month_b: int
    year_b: int


class PdfRequest(BaseModel):
    full_name: str
    profile: dict
    life_areas: dict
    pinnacles: dict
    challenges: dict
    karmic_lessons: list


class EnquiryRequest(BaseModel):
    product: str
    name: str
    contact: str
    message: str = ""


class BookingRequest(BaseModel):
    service: str
    duration: str
    price: str
    preferred_date: str
    preferred_time: str
    name: str
    contact: str
    notes: str = ""


class CourseEnquiryRequest(BaseModel):
    course: str
    name: str
    contact: str
    message: str = ""


class EbookEnquiryRequest(BaseModel):
    ebook: str
    name: str
    contact: str
    message: str = ""


# ---------- Lightweight endpoints (no AI libraries loaded) ----------

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Numerology AI Insights API"}


@app.post("/api/profile")
def get_profile(req: ProfileRequest):
    """Calculate the full numerology profile — pure calculation, no AI."""
    profile = get_full_numerology_profile(req.full_name, req.day, req.month, req.year)
    profile["maturity_number"] = calculate_maturity_number(
        req.day, req.month, req.year, req.full_name
    )
    breakdown = get_life_path_breakdown(req.day, req.month, req.year)
    pinnacles = calculate_pinnacles(req.day, req.month, req.year)
    challenges = calculate_challenges(req.day, req.month, req.year)
    karmic_lessons = calculate_karmic_lessons(req.full_name)

    return {
        "profile": profile,
        "life_path_breakdown": breakdown,
        "pinnacles": pinnacles,
        "challenges": challenges,
        "karmic_lessons": karmic_lessons,
    }


@app.post("/api/pdf-report")
def pdf_report(req: PdfRequest):
    """Generate and return the PDF report — no AI called here, just formatting
    already-generated content (the life_areas dict is passed in from the client,
    generated earlier via /api/life-areas)."""
    combined_interpretation = "\n\n".join(
        f"## {key}\n{value}" for key, value in req.life_areas.items()
    )
    pdf_bytes = generate_pdf_report(
        req.full_name, req.profile, combined_interpretation,
        pinnacles=req.pinnacles, challenges=req.challenges,
        karmic_lessons=req.karmic_lessons,
    )
    filename = f"{req.full_name.replace(' ', '_')}_numerology_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/shop-enquiry")
def shop_enquiry(req: EnquiryRequest):
    if not req.name.strip() or not req.contact.strip():
        raise HTTPException(status_code=400, detail="Name and contact are required.")
    leads_file = Path("shop_enquiries.csv")
    is_new_file = not leads_file.exists()
    with open(leads_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow(["timestamp", "product", "name", "contact", "message"])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            req.product, req.name, req.contact, req.message,
        ])
    return {"status": "saved"}


@app.post("/api/booking")
def create_booking(req: BookingRequest):
    if not req.name.strip() or not req.contact.strip():
        raise HTTPException(status_code=400, detail="Name and contact are required.")
    bookings_file = Path("bookings.csv")
    is_new_file = not bookings_file.exists()
    with open(bookings_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow([
                "timestamp", "service", "duration", "price",
                "preferred_date", "preferred_time", "name", "contact", "notes",
                "status",
            ])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            req.service, req.duration, req.price,
            req.preferred_date, req.preferred_time,
            req.name, req.contact, req.notes,
            "pending_confirmation",
        ])
    return {"status": "saved"}


@app.post("/api/course-enquiry")
def course_enquiry(req: CourseEnquiryRequest):
    if not req.name.strip() or not req.contact.strip():
        raise HTTPException(status_code=400, detail="Name and contact are required.")
    leads_file = Path("course_enquiries.csv")
    is_new_file = not leads_file.exists()
    with open(leads_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow(["timestamp", "course", "name", "contact", "message"])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            req.course, req.name, req.contact, req.message,
        ])
    return {"status": "saved"}


@app.post("/api/ebook-enquiry")
def ebook_enquiry(req: EbookEnquiryRequest):
    if not req.name.strip() or not req.contact.strip():
        raise HTTPException(status_code=400, detail="Name and contact are required.")
    leads_file = Path("ebook_enquiries.csv")
    is_new_file = not leads_file.exists()
    with open(leads_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow(["timestamp", "ebook", "name", "contact", "message"])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            req.ebook, req.name, req.contact, req.message,
        ])
    return {"status": "saved"}


# ---------- AI-dependent endpoints (heavy stack loaded lazily, on first call) ----------

@app.post("/api/life-areas")
def get_life_areas(req: ProfileRequest):
    """Generate the full AI-powered life areas interpretation. This is
    where LangChain/ChromaDB/google-generativeai actually get imported —
    only when this specific endpoint is called."""
    from services.gemini_service import generate_life_areas_profile

    profile = get_full_numerology_profile(req.full_name, req.day, req.month, req.year)
    profile["maturity_number"] = calculate_maturity_number(
        req.day, req.month, req.year, req.full_name
    )
    try:
        life_areas = generate_life_areas_profile(req.full_name, profile)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {e}")

    return {"life_areas": life_areas}


@app.post("/api/chat")
def chat(req: ChatRequest):
    """Answer a follow-up question about the person's numerology profile."""
    from services.gemini_service import answer_numerology_question

    try:
        answer = answer_numerology_question(
            req.full_name, req.profile, req.question, req.chat_history
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {e}")

    return {"answer": answer}


@app.post("/api/compatibility")
def compatibility(req: CompatibilityRequest):
    """Calculate compatibility scores and generate an AI explanation."""
    from services.gemini_service import generate_compatibility_explanation

    compat = calculate_compatibility(
        req.name_a, req.day_a, req.month_a, req.year_a,
        req.name_b, req.day_b, req.month_b, req.year_b,
    )
    try:
        explanation = generate_compatibility_explanation(compat)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {e}")

    return {"compatibility": compat, "explanation": explanation}


# ---------- Serve the frontend ----------
# Mounted LAST, after all /api/* routes above, so those routes match first.
# This serves frontend/index.html at "/", plus style.css and script.js,
# directly from this same service — one URL, one deployment, no more
# cross-origin API_BASE mismatches.
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")