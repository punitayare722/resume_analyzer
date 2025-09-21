# AI Resume Analyser



**AI Resume Analyser** is a web application that evaluates your existing resume against a target job description. It provides insights into your current skills, highlights missing skills, calculates a skill match percentage, and generates a roadmap for skill improvement. This project demonstrates skills in data analysis, AI integration, and full-stack development.

---

## Features

- Upload existing resume in PDF format.  
- Input a **Job Description** for comparison.  
- AI analyzes your resume to identify:  
  - Existing skills  
  - Missing skills  
  - Skill match percentage  
- Generates a **personalized roadmap** to improve skill alignment with the target job.  
- Provides downloadable report (PDF) with insights and recommendations.  

---

## Tech Stack

- **Frontend:** React.js  
- **Backend:** FastAPI  
- **AI Integration:** Groq API LLM  
- **Data Analysis:** Python (Pandas, NumPy, Scikit-learn)  
- **PDF Generation:** ReportLab, PyMuPDF  

---

## Project Structure

---

## Getting Started

### Prerequisites

- Python 3.10+  
- Node.js & npm  
- Groq API key  
- Git  

---




---
###1. Clone your repository
# ------------------------------
```
git clone https://github.com/punitayare722/resume_analyzer.git
cd resume_analyzer
```
# ------------------------------
# 2. Backend Setup
# ------------------------------
```
cd backend
```
# Create virtual environment
```
python -m venv venv
```
# Activate virtual environment
# Windows
```
venv\Scripts\activate
```
# macOS/Linux
```
# source venv/bin/activate
```

# Install dependencies
```
pip install -r requirements.txt
```
# Create .env file with Groq API key
```
echo "GROQ_API_KEY=your_groq_api_key_here" > .env
```
# Run FastAPI server
```
uvicorn app.main:app --reload
# Backend will run at http://127.0.0.1:8000
```
# ------------------------------
# 3. Frontend Setup
# ------------------------------
```
cd ../frontend/resume-frontend
```
# Install dependencies
```
npm install
```

# Start React development server
```
npm start
```
# Frontend will run at http://localhost:3000

# ------------------------------
# 4. Usage
# ------------------------------
# 1. Open frontend in browser: http://localhost:3000
# 2. Upload your existing PDF resume.
# 3. Enter the target job description.
# 4. Click "Analyze Resume".
# 5. Review skill match %, missing skills, and roadmap.
# 6. Download PDF report with detailed analysis.

# ------------------------------
# 5. Optional: Deactivate Backend Environment
# ------------------------------
deactivate




