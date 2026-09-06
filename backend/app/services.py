from pathlib import Path
import base64
import hashlib
import io
from datetime import datetime

import qrcode

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.units import mm

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    Image,
)

from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# ---------------------------------------------------------
# DIRECTORIES
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "generated"
KEY_DIR = BASE_DIR / "keys"

OUTPUT_DIR.mkdir(exist_ok=True)
KEY_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------
# FONTS
# ---------------------------------------------------------

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

# Optional corporate font support
font_regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
font_bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

if font_regular.exists() and font_bold.exists():
    try:
        pdfmetrics.registerFont(
            TTFont("CorporateRegular", str(font_regular))
        )
        pdfmetrics.registerFont(
            TTFont("CorporateBold", str(font_bold))
        )

        FONT_REGULAR = "CorporateRegular"
        FONT_BOLD = "CorporateBold"
    except Exception:
        pass


# ---------------------------------------------------------
# RSA KEY GENERATION
# ---------------------------------------------------------

PRIVATE_KEY_FILE = KEY_DIR / "private_key.pem"
PUBLIC_KEY_FILE = KEY_DIR / "public_key.pem"


def ensure_keys():
    """
    Generate RSA keys if they don't already exist.
    """

    if PRIVATE_KEY_FILE.exists() and PUBLIC_KEY_FILE.exists():
        return

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    PRIVATE_KEY_FILE.write_bytes(private_bytes)
    PUBLIC_KEY_FILE.write_bytes(public_bytes)


# ---------------------------------------------------------
# DIGITAL SIGNATURE
# ---------------------------------------------------------

def sign_offer(data: str) -> str:
    """
    Create RSA digital signature for offer data.
    """

    ensure_keys()

    private_key = serialization.load_pem_private_key(
        PRIVATE_KEY_FILE.read_bytes(),
        password=None,
    )

    signature = private_key.sign(
        data.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    return base64.b64encode(signature).decode("utf-8")


def verify(data: str, signature_b64: str) -> bool:
    """
    Verify RSA digital signature.
    """

    try:
        ensure_keys()

        public_key = serialization.load_pem_public_key(
            PUBLIC_KEY_FILE.read_bytes()
        )

        signature = base64.b64decode(signature_b64)

        public_key.verify(
            signature,
            data.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )

        return True

    except Exception:
        return False

# ---------------------------------------------------------
# OFFER HASH
# ---------------------------------------------------------

def generate_offer_hash(offer) -> str:
    """
    Generate the exact canonical data used for
    digital signature and verification.

    IMPORTANT:
    This exact string is used both when signing the offer
    and when verifying the offer.
    """

    data = (
        f"{offer.offer_number}|"
        f"{offer.candidate_name}|"
        f"{offer.email}|"
        f"{offer.designation}|"
        f"{offer.joining_date}|"
        f"{offer.ctc}|"
        f"{offer.work_location}"
    )

    return data


# ---------------------------------------------------------
# PDF PAGE HEADER / FOOTER
# ---------------------------------------------------------

def draw_header_footer(canvas, doc):
    canvas.saveState()

    width, height = A4

    # Top corporate line
    canvas.setStrokeColor(colors.HexColor("#1F3A5F"))
    canvas.setLineWidth(2)
    canvas.line(
        20 * mm,
        height - 17 * mm,
        width - 20 * mm,
        height - 17 * mm,
    )

    # Footer line
    canvas.setStrokeColor(colors.HexColor("#D5D9DE"))
    canvas.setLineWidth(0.5)

    canvas.line(
        20 * mm,
        15 * mm,
        width - 20 * mm,
        15 * mm,
    )

    # Footer text
    canvas.setFont(FONT_REGULAR, 7)
    canvas.setFillColor(colors.HexColor("#6B7280"))

    canvas.drawString(
        20 * mm,
        9 * mm,
        "Confidential • Human Resources Department",
    )

    canvas.drawRightString(
        width - 20 * mm,
        9 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


# ---------------------------------------------------------
# HELPER
# ---------------------------------------------------------

def safe(value, default=""):
    if value is None:
        return default

    return str(value)


def money(value):
    try:
        amount = float(value)
        return f"₹{amount:,.2f}"
    except Exception:
        return safe(value)


# ---------------------------------------------------------
# GENERATE PDF
# ---------------------------------------------------------

def generate_pdf(o):
    """
    Generate professional corporate offer letter PDF.
    """

    ensure_keys()

    offer_number = safe(
        getattr(o, "offer_number", ""),
        f"OFF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
    )

    pdf_path = OUTPUT_DIR / f"{offer_number}.pdf"

    # -----------------------------------------------------
    # DOCUMENT
    # -----------------------------------------------------

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=25 * mm,
        bottomMargin=22 * mm,
        title=f"Offer Letter - {offer_number}",
        author=safe(
            getattr(o, "company_name", ""),
            "Human Resources",
        ),
    )

    # -----------------------------------------------------
    # STYLES
    # -----------------------------------------------------

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CorporateTitle",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1F3A5F"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    company_style = ParagraphStyle(
        "Company",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1F3A5F"),
        alignment=TA_LEFT,
    )

    normal_style = ParagraphStyle(
        "CorporateNormal",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=9.5,
        leading=15,
        textColor=colors.HexColor("#20262E"),
        alignment=TA_LEFT,
        spaceAfter=7,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#5B6470"),
    )

    bold_style = ParagraphStyle(
        "Bold",
        parent=normal_style,
        fontName=FONT_BOLD,
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1F3A5F"),
        spaceBefore=7,
        spaceAfter=6,
    )

    subject_style = ParagraphStyle(
        "Subject",
        parent=normal_style,
        fontName=FONT_BOLD,
        fontSize=10,
        textColor=colors.HexColor("#111827"),
        spaceAfter=12,
    )

    center_small = ParagraphStyle(
        "CenterSmall",
        parent=small_style,
        alignment=TA_CENTER,
    )

    # -----------------------------------------------------
    # DATA
    # -----------------------------------------------------

    company_name = safe(
        getattr(o, "company_name", ""),
        "Company",
    )

    company_address = safe(
        getattr(o, "company_address", ""),
        "Corporate Office",
    )

    company_email = safe(
        getattr(o, "company_email", ""),
    )

    company_phone = safe(
        getattr(o, "company_phone", ""),
    )

    candidate_name = safe(
        getattr(o, "candidate_name", ""),
    )

    candidate_address = safe(
        getattr(o, "candidate_address", ""),
    )

    candidate_email = safe(
        getattr(o, "email", ""),
    )

    candidate_phone = safe(
        getattr(o, "phone", ""),
    )

    designation = safe(
        getattr(o, "designation", ""),
    )

    department = safe(
        getattr(o, "department", ""),
    )

    joining_date = safe(
        getattr(o, "joining_date", ""),
    )

    work_location = safe(
        getattr(o, "work_location", ""),
    )

    employment_type = safe(
        getattr(o, "employment_type", ""),
        "Full Time",
    )

    ctc = getattr(o, "ctc", 0)

    probation_period = safe(
        getattr(o, "probation_period", ""),
        "6 months",
    )

    notice_period = safe(
        getattr(o, "notice_period", ""),
        "30 days",
    )

    reporting_to = safe(
        getattr(o, "reporting_to", ""),
        "Department Manager",
    )

    hr_name = safe(
        getattr(o, "hr_name", ""),
        "Human Resources",
    )

    # -----------------------------------------------------
    # OFFER HASH + SIGNATURE
    # -----------------------------------------------------

    offer_hash = generate_offer_hash(o)

    signature = sign_offer(offer_hash)

    # -----------------------------------------------------
    # STORY
    # -----------------------------------------------------

    story = []

    # -----------------------------------------------------
    # CORPORATE HEADER
    # -----------------------------------------------------

    header_left = [
        Paragraph(
            company_name,
            company_style,
        ),
        Paragraph(
            company_address,
            small_style,
        ),
    ]

    contact_text = "<br/>".join(
        x for x in [
            company_email,
            company_phone,
        ]
        if x
    )

    header_right = [
        Paragraph(
            "HUMAN RESOURCES",
            ParagraphStyle(
                "HRHeader",
                parent=small_style,
                fontName=FONT_BOLD,
                fontSize=8.5,
                textColor=colors.HexColor("#1F3A5F"),
                alignment=TA_LEFT,
            ),
        ),
        Paragraph(
            contact_text,
            small_style,
        ),
    ]

    header_table = Table(
        [[header_left, header_right]],
        colWidths=[
            110 * mm,
            60 * mm,
        ],
    )

    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(header_table)

    story.append(
        Spacer(1, 12 * mm)
    )

    # -----------------------------------------------------
    # DATE / REFERENCE
    # -----------------------------------------------------

    current_date = datetime.now().strftime("%d %B %Y")

    reference_table = Table(
        [
            [
                Paragraph(
                    f"<b>Date:</b> {current_date}",
                    small_style,
                ),
                Paragraph(
                    f"<b>Offer Reference:</b> {offer_number}",
                    small_style,
                ),
            ]
        ],
        colWidths=[
            85 * mm,
            85 * mm,
        ],
    )

    reference_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(reference_table)

    story.append(
        Spacer(1, 8 * mm)
    )

    # -----------------------------------------------------
    # CANDIDATE ADDRESS
    # -----------------------------------------------------

    candidate_block = [
        Paragraph(
            f"<b>{candidate_name}</b>",
            bold_style,
        ),
    ]

    if candidate_address:
        candidate_block.append(
            Paragraph(
                candidate_address,
                normal_style,
            )
        )

    if candidate_email:
        candidate_block.append(
            Paragraph(
                candidate_email,
                small_style,
            )
        )

    if candidate_phone:
        candidate_block.append(
            Paragraph(
                candidate_phone,
                small_style,
            )
        )

    story.extend(candidate_block)

    story.append(
        Spacer(1, 5 * mm)
    )

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "OFFER OF EMPLOYMENT",
            title_style,
        )
    )

    story.append(
        Paragraph(
            f"Subject: Offer of Employment for the position of {designation}",
            subject_style,
        )
    )

    # -----------------------------------------------------
    # SALUTATION
    # -----------------------------------------------------

    story.append(
        Paragraph(
            f"Dear {candidate_name},",
            normal_style,
        )
    )

    # -----------------------------------------------------
    # INTRODUCTION
    # -----------------------------------------------------

    story.append(
        Paragraph(
            f"""
            We are pleased to offer you employment with
            <b>{company_name}</b> for the position of
            <b>{designation}</b> in the <b>{department}</b> department.
            Based on your qualifications, experience and discussions
            during the selection process, we believe that you will be
            a valuable addition to our organization.
            """,
            normal_style,
        )
    )

    story.append(
        Paragraph(
            f"""
            Your proposed date of joining will be
            <b>{joining_date}</b>. You will be based at
            <b>{work_location}</b> and will report to
            <b>{reporting_to}</b>.
            """,
            normal_style,
        )
    )

    # -----------------------------------------------------
    # APPOINTMENT DETAILS
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "1. APPOINTMENT DETAILS",
            section_style,
        )
    )

    appointment_data = [
        [
            Paragraph("<b>Position</b>", small_style),
            Paragraph(designation, small_style),
        ],
        [
            Paragraph("<b>Department</b>", small_style),
            Paragraph(department, small_style),
        ],
        [
            Paragraph("<b>Employment Type</b>", small_style),
            Paragraph(employment_type, small_style),
        ],
        [
            Paragraph("<b>Date of Joining</b>", small_style),
            Paragraph(joining_date, small_style),
        ],
        [
            Paragraph("<b>Work Location</b>", small_style),
            Paragraph(work_location, small_style),
        ],
        [
            Paragraph("<b>Reporting To</b>", small_style),
            Paragraph(reporting_to, small_style),
        ],
    ]

    appointment_table = Table(
        appointment_data,
        colWidths=[
            55 * mm,
            115 * mm,
        ],
        repeatRows=0,
    )

    appointment_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#F3F6F9"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D6DCE3"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(appointment_table)

    story.append(
        Spacer(1, 5 * mm)
    )

    # -----------------------------------------------------
    # COMPENSATION
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "2. COMPENSATION",
            section_style,
        )
    )

    try:
        annual_ctc = float(ctc)
    except Exception:
        annual_ctc = 0

    basic = annual_ctc * 0.40
    hra = annual_ctc * 0.20
    special = annual_ctc * 0.30
    benefits = annual_ctc * 0.10

    compensation_data = [
        [
            Paragraph("<b>Component</b>", small_style),
            Paragraph("<b>Annual Amount</b>", small_style),
            Paragraph("<b>% of CTC</b>", small_style),
        ],
        [
            Paragraph("Basic Salary", small_style),
            Paragraph(money(basic), small_style),
            Paragraph("40%", small_style),
        ],
        [
            Paragraph("House Rent Allowance", small_style),
            Paragraph(money(hra), small_style),
            Paragraph("20%", small_style),
        ],
        [
            Paragraph("Special Allowance", small_style),
            Paragraph(money(special), small_style),
            Paragraph("30%", small_style),
        ],
        [
            Paragraph("Employer Benefits / PF", small_style),
            Paragraph(money(benefits), small_style),
            Paragraph("10%", small_style),
        ],
        [
            Paragraph("<b>Total Annual CTC</b>", small_style),
            Paragraph(f"<b>{money(annual_ctc)}</b>", small_style),
            Paragraph("<b>100%</b>", small_style),
        ],
    ]

    compensation_table = Table(
        compensation_data,
        colWidths=[
            85 * mm,
            55 * mm,
            30 * mm,
        ],
    )

    compensation_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1F3A5F"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "BACKGROUND",
                    (0, -1),
                    (-1, -1),
                    colors.HexColor("#EAF0F6"),
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D6DCE3"),
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(compensation_table)

    story.append(
        Paragraph(
            f"""
            Your total annual Cost to Company (CTC) will be
            <b>{money(annual_ctc)}</b>. The compensation structure
            may be subject to applicable statutory deductions,
            taxes and company policies.
            """,
            normal_style,
        )
    )

    # -----------------------------------------------------
    # PAGE BREAK
    # -----------------------------------------------------

    story.append(PageBreak())

    # -----------------------------------------------------
    # PAGE 2 TITLE
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "TERMS & CONDITIONS OF EMPLOYMENT",
            title_style,
        )
    )

    # -----------------------------------------------------
    # TERMS
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "3. PROBATION",
            section_style,
        )
    )

    story.append(
        Paragraph(
            f"""
            Your initial probation period will be
            <b>{probation_period}</b> from the date of joining.
            During this period, your performance, conduct and
            suitability for the role will be evaluated.
            """,
            normal_style,
        )
    )

    story.append(
        Paragraph(
            "4. NOTICE PERIOD",
            section_style,
        )
    )

    story.append(
        Paragraph(
            f"""
            The applicable notice period will be
            <b>{notice_period}</b>, subject to the terms of your
            employment agreement and prevailing company policy.
            """,
            normal_style,
        )
    )

    story.append(
        Paragraph(
            "5. COMPANY POLICIES",
            section_style,
        )
    )

    story.append(
        Paragraph(
            """
            You will be required to comply with all company
            policies, procedures, information-security requirements,
            code of conduct, confidentiality obligations and other
            applicable rules communicated by the organization from
            time to time.
            """,
            normal_style,
        )
    )

    story.append(
        Paragraph(
            "6. CONFIDENTIALITY",
            section_style,
        )
    )

    story.append(
        Paragraph(
            """
            During and after your employment, you must maintain
            strict confidentiality regarding business information,
            customer information, intellectual property, financial
            information, technical information and any other
            confidential information belonging to the organization.
            """,
            normal_style,
        )
    )

    story.append(
        Paragraph(
            "7. DOCUMENT VERIFICATION",
            section_style,
        )
    )

    story.append(
        Paragraph(
            """
            This offer is subject to successful verification of the
            information and documents provided by you during the
            recruitment process. Any material discrepancy or
            misrepresentation may result in withdrawal of the offer
            or termination of employment in accordance with applicable
            company policy and law.
            """,
            normal_style,
        )
    )

    story.append(
        Paragraph(
            "8. ACCEPTANCE OF OFFER",
            section_style,
        )
    )

    story.append(
        Paragraph(
            """
            Please sign and return a copy of this offer letter as
            confirmation of your acceptance of the terms stated
            herein. We look forward to welcoming you to our team and
            wish you a successful and rewarding career with the
            organization.
            """,
            normal_style,
        )
    )

    # -----------------------------------------------------
    # SIGNATURE SECTION
    # -----------------------------------------------------

    story.append(
        Spacer(1, 7 * mm)
    )

    signature_data = [
        [
            Paragraph(
                "For and on behalf of",
                small_style,
            ),
            "",
        ],
        [
            Paragraph(
                f"<b>{company_name}</b>",
                bold_style,
            ),
            "",
        ],
        [
            Spacer(1, 12 * mm),
            "",
        ],
        [
            Paragraph(
                f"<b>{hr_name}</b>",
                small_style,
            ),
            Paragraph(
                f"<b>{candidate_name}</b>",
                small_style,
            ),
        ],
        [
            Paragraph(
                "Authorized HR Representative",
                small_style,
            ),
            Paragraph(
                "Candidate Acceptance",
                small_style,
            ),
        ],
    ]

    signature_table = Table(
        signature_data,
        colWidths=[
            85 * mm,
            85 * mm,
        ],
    )

    signature_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LINEABOVE",
                    (0, 3),
                    (0, 3),
                    0.7,
                    colors.HexColor("#7B8794"),
                ),
                (
                    "LINEABOVE",
                    (1, 3),
                    (1, 3),
                    0.7,
                    colors.HexColor("#7B8794"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    0,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    story.append(signature_table)

    # -----------------------------------------------------
    # DIGITAL VERIFICATION
    # -----------------------------------------------------

    story.append(
        Spacer(1, 7 * mm)
    )

    story.append(
        Paragraph(
            "DIGITAL AUTHENTICITY & VERIFICATION",
            section_style,
        )
    )

    # -----------------------------------------------------
    # QR CODE
    # -----------------------------------------------------

    qr = qrcode.make(
        f"http://127.0.0.1:8000/api/offers/verify/{offer_number}"
    )

    qr_path = OUTPUT_DIR / f"{offer_number}_qr.png"

    qr.save(str(qr_path))

    # IMPORTANT:
    # Use actual file path with ReportLab Image.
    # This avoids ImageReader / BytesIO compatibility issues.
    q = Image(
        str(qr_path),
        width=30 * mm,
        height=30 * mm,
    )

    verification_text = Paragraph(
        f"""
        <b>Offer Reference:</b> {offer_number}<br/>
        <b>Document Hash:</b> {offer_hash[:32]}...<br/>
        <b>Digital Signature:</b> RSA-2048 / SHA-256<br/>
        <b>Status:</b> Digitally Signed<br/>
        <br/>
        Scan the QR code to verify this offer letter through the
        organization's verification service.
        """,
        small_style,
    )

    verification_table = Table(
        [
            [
                q,
                verification_text,
            ]
        ],
        colWidths=[
            40 * mm,
            130 * mm,
        ],
    )

    verification_table.setStyle(
        TableStyle(
            [
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    colors.HexColor("#C8D0D9"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F7F9FB"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.append(verification_table)

    # -----------------------------------------------------
    # SIGNATURE HASH
    # -----------------------------------------------------

    story.append(
        Spacer(1, 5 * mm)
    )

    story.append(
        Paragraph(
            f"""
            <b>Digital Signature:</b>
            {signature[:70]}...
            """,
            center_small,
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        Paragraph(
            "This is a system-generated digitally signed document.",
            center_small,
        )
    )

    # -----------------------------------------------------
    # BUILD PDF
    # -----------------------------------------------------

    doc.build(
        story,
        onFirstPage=draw_header_footer,
        onLaterPages=draw_header_footer,
    )

    return str(pdf_path), signature
