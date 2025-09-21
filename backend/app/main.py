# app/main.py
from fastapi import FastAPI, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import fitz  # PyMuPDF
import io
import json
from groq import Groq
from dotenv import load_dotenv
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
import app.api.v1.auth as auth
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from jinja2 import Environment, FileSystemLoader

# app/main.py
from fastapi import FastAPI, UploadFile, Form, Depends
from fastapi.responses import FileResponse
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import app.api.v1.auth as auth
from fastapi.responses import StreamingResponse
# Load API key
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables!")

client = Groq(api_key=API_KEY)

# Initialize FastAPI
app = FastAPI(title="Resume Analyzer API")

# Include authentication router
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# CORS
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- PDF text extraction ----------
def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# ---------- Analyze Resume ----------
@app.post("/analyze_resume")
async def analyze_resume(
    resume: UploadFile, 
    jd: str = Form(...),
    current_user=Depends(auth.get_current_user)  # Protect route
):
    file_bytes = await resume.read()
    resume_text = extract_text_from_pdf(file_bytes)

    prompt = f"""
You are a career coach.
Compare the following resume and job description.

Resume:
{resume_text}

Job Description:
{jd}

Respond ONLY in valid JSON (no explanations, no markdown) with:
- existing_skills: list of skills already present in resume
- missing_skills: list of skills missing compared to JD
- roadmap: list of objects for 1–6 month plan, each with fields 'month', 'task', 'resource'
- recommendations: list of actionable recommendations
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    raw_output = response.choices[0].message.content.strip()
    try:
        if raw_output.startswith("```"):
            raw_output = raw_output.strip("```json").strip("```").strip()
        parsed_analysis = json.loads(raw_output)
    except Exception as e:
        parsed_analysis = {"error": str(e), "raw_text": raw_output}

    return {"analysis": parsed_analysis}




@app.post("/edit_resume")
async def edit_resume(
    resume: UploadFile,
    suggestions: str = Form(...),
    template: str = Form("default"),
    current_user=Depends(auth.get_current_user)
):
    # Extract text from uploaded PDF
    file_bytes = await resume.read()
    resume_text = extract_text_from_pdf(file_bytes)

    # AI-generated improved content
    prompt = f"""
You are a resume expert.
Current resume text:
{resume_text}

Suggestions:
{suggestions}

Output an updated resume text according to the suggestions and selected template: {template}.
Return only text, structured with headings (like 'Summary', 'Skills', 'Experience', 'Projects', 'Certifications', 'Education').
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    improved_resume = response.choices[0].message.content.strip()

    # Generate PDF using platypus
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    section_title = ParagraphStyle(
        "SectionTitle", parent=styles["Heading2"], fontSize=14, spaceAfter=10, textColor="#003366"
    )
    body_text = styles["Normal"]

    for line in improved_resume.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 12))
            continue
        if line.endswith(":") or line.lower() in ["summary", "skills", "experience", "projects", "certifications", "education"]:
            story.append(Paragraph(line, section_title))
        else:
            story.append(Paragraph(line, body_text))

    doc.build(story)
    buffer.seek(0)

    output_file = f"optimized_resume_{template}.pdf"
    with open(output_file, "wb") as f:
        f.write(buffer.getvalue())

    return FileResponse(output_file, media_type="application/pdf", filename=f"optimized_resume_{template}.pdf")

env = Environment(loader=FileSystemLoader("templates"))










# ---------- Call Groq LLM to rewrite resume ----------
def ai_generate_resume(resume_text: str, jd: str) -> dict:
    prompt = f"""
You are a career assistant AI. Rewrite the following resume to best match the given job description.
Keep it truthful, professional, ATS-friendly, and in structured format.

Resume:
{resume_text}

Job Description:
{jd}

Return only JSON in the format:
{{
  "Summary": "...",
  "Skills": ["...", "..."],
  "Experience": ["...", "..."],
  "Projects": ["...", "..."],
  "Education": ["...", "..."],
  "Certifications": ["...", "..."]
}}
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    raw_output = response.choices[0].message.content.strip()

    if raw_output.startswith("```"):
        raw_output = raw_output.strip("```json").strip("```").strip()

    try:
        structured_resume = json.loads(raw_output)
    except json.JSONDecodeError:
        # fallback if AI output is invalid
        structured_resume = {
            "Summary": resume_text[:1000],
            "Skills": [],
            "Experience": [],
            "Projects": [],
            "Education": [],
            "Certifications": []
        }
    return structured_resume

# ---------- Styled Resume PDF ----------
def generate_resume_pdf(resume_data: dict, template: str = "default") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    # Template styles
    if template == "default":
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#003366"), spaceAfter=12)
        header_style = ParagraphStyle("Header", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#003366"), spaceAfter=6)
        body_style = styles["Normal"]
    elif template == "modern":
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#0D47A1"), spaceAfter=14)
        header_style = ParagraphStyle("Header", parent=styles["Heading2"], fontSize=12, textColor=colors.HexColor("#1565C0"), spaceAfter=4, underlineWidth=1)
        body_style = styles["Normal"]
    elif template == "creative":
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=22, textColor=colors.HexColor("#FF5722"), spaceAfter=16)
        header_style = ParagraphStyle("Header", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#FF7043"), spaceAfter=6, backColor=colors.HexColor("#FFE0B2"))
        body_style = styles["Normal"]
    else:
        title_style = styles["Heading1"]
        header_style = styles["Heading2"]
        body_style = styles["Normal"]

    # Add Name & Contact (optional: can also come from AI)
    story.append(Paragraph("John Doe", title_style))
    story.append(Paragraph("Email: john@example.com | Phone: +91 1234567890", body_style))
    story.append(Spacer(1, 12))

    # Add all sections
    for section in ["Summary", "Skills", "Experience", "Projects", "Education", "Certifications"]:
        content = resume_data.get(section)
        if not content:
            continue
        story.append(Paragraph(section, header_style))
        if isinstance(content, list):
            for item in content:
                story.append(Paragraph(f"• {item}", body_style))
        else:
            story.append(Paragraph(content, body_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ---------- FastAPI endpoint ----------
@app.post("/optimize_resume")
async def optimize_resume(
    resume: UploadFile,
    jd: str = Form(...),
    template: str = Form("default"),
    current_user=Depends(auth.get_current_user)
):
    file_bytes = await resume.read()
    resume_text = extract_text_from_pdf(file_bytes)

    structured_resume = ai_generate_resume(resume_text, jd)
    pdf_bytes = generate_resume_pdf(structured_resume, template)

    return FileResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", filename=f"resume_{template}.pdf")
