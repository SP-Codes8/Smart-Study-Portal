from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db, engine
from models import Base, Student,Parent,Summary
from schemas import StudentCreate,StudentUpdate
from auth import get_current_user
from typing import List
from auth import hash_password,verify_password
from schemas import ParentCreate
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import json
import re
from PIL import Image
import io
from dotenv import load_dotenv
import pytesseract
from database import SessionLocal
from fastapi.responses import JSONResponse

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="SmartStudy AI")

origins = [
    "http://localhost:3000",  # React dev server
    "http://127.0.0.1:3000",  # Sometimes browsers use this
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify ["http://localhost:3000"] for security
    allow_credentials=True,
    allow_methods=["*"],  # Allows POST, GET, PUT, DELETE, OPTIONS
    allow_headers=["*"],  # Allows all headers like Content-Type, Authorization
)

# Create database tables
Base.metadata.create_all(bind=engine)

# -------------------------------
# STUDENT APIs
# -------------------------------



# -------------------------------
# Register Student
# -------------------------------
@app.post("/students/register")
def register_student(student: StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.register_no == student.register_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already exists with this registration number.")

    # ✅ Hash the password before storing
    hashed_pwd = hash_password(student.password)

    new_student = Student(
        name=student.name,
        parent_name=student.parent_name,
        register_no=student.register_no,
        student_class=student.student_class,
        password=hashed_pwd
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return {"message": "Student registered successfully"}
@app.post("/students/login")
def student_login(data: dict, db: Session = Depends(get_db)):
    reg_no = data.get("register_no")
    password = data.get("password")

    student = db.query(Student).filter(Student.register_no == reg_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if not verify_password(password, student.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "message": "Login successful",
        "student": {
            "register_no": student.register_no,
            "name": student.name,
            "class": student.student_class,
            "parent_name": student.parent_name
        }
    }
# -------------------------------
# Get All Students
# -------------------------------
@app.get("/students", response_model=List[dict])
def get_all_students(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Fetch all students (admin/parent access)"""
    students = db.query(Student).all()
    return [
        {
            "register_no": s.register_no,
            "name": s.name,
            "class": s.student_class,
            "parent_name": s.parent_name
        }
        for s in students
    ]

# -------------------------------
# Get Student by Register Number
# -------------------------------
@app.get("/students/{register_no}", response_model=dict)
def get_student(register_no: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Fetch student by registration number"""
    student = db.query(Student).filter(Student.register_no == register_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {
        "register_no": student.register_no,
        "name": student.name,
        "class": student.student_class,
        "parent_name": student.parent_name
    }

# -------------------------------
# Update Student by Register Number
# -------------------------------
@app.put("/students/{register_no}", response_model=dict)
def update_student(register_no: str, student_data: StudentUpdate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Update student details"""
    student = db.query(Student).filter(Student.register_no == register_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    for key, value in student_data.dict(exclude_unset=True).items():
        setattr(student, key, value)

    db.commit()
    db.refresh(student)
    return {"message": "Student updated successfully"}

# -------------------------------
# Delete Student by Register Number
# -------------------------------
@app.delete("/students/{register_no}", response_model=dict)
def delete_student(register_no: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Delete student by registration number"""
    student = db.query(Student).filter(Student.register_no == register_no).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()
    return {"message": "Student deleted successfully"}
@app.post("/parents/register")
def register_parent(parent: ParentCreate, db: Session = Depends(get_db)):
    existing = db.query(Parent).filter(Parent.email == parent.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Parent already exists with this email.")

    hashed_pwd = hash_password(parent.password)

    new_parent = Parent(
        parent_name=parent.parent_name,
        phone_number=parent.phone_number,
        email=parent.email,
        password=hashed_pwd
    )

    db.add(new_parent)
    db.commit()
    db.refresh(new_parent)

    return {"message": "Parent registered successfully"}


@app.post("/parents/login")
def parent_login(data: dict, db: Session = Depends(get_db)):
    email = data.get("email")
    password = data.get("password")

    parent = db.query(Parent).filter(Parent.email == email).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    if not verify_password(password, parent.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "message": "Login successful",
        "parent": {
            "parent_name": parent.parent_name,
            "phone_number": parent.phone_number,
            "email": parent.email
        }
    }

# -------------------------------
# IMAGE PROCESSING API
# -------------------------------

# Configure Gemini API (v1beta) - Only for summarization and MCQ generation
# Load API key from .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Configure Tesseract OCR path (if needed on Windows)
# Uncomment and set the path if Tesseract is not in your system PATH
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
@app.post("/process-image")
async def process_image(file: UploadFile = File(...)):
    """
    Process uploaded image: Extract text using OCR (Tesseract),
    generate summary + MCQs using Gemini, and store the image in DB.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Gemini API key not configured. Please set GEMINI_API_KEY environment variable.",
        )

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    db: Session = SessionLocal()

    try:
        # Read image file
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))

        # Extract text from image using Tesseract
        extracted_text = pytesseract.image_to_string(image, lang="eng")

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the image. Please ensure the image contains clear text.",
            )

        # Generate summary using Gemini 2.5 Flash
        model = genai.GenerativeModel("gemini-2.5-flash")
        summary_response = model.generate_content(
            f"Please provide a concise summary of the following textbook content:\n\n{extracted_text}"
        )
        summary = summary_response.text

        # Generate MCQ questions
        mcq_prompt = f"""
Based on the following summary, generate 5 multiple choice questions (MCQs) with 4 options each.

Summary:
{summary}

Format the response as a JSON array:
[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option A"
  }}
]
Return ONLY the JSON array.
"""
        mcq_response = model.generate_content(mcq_prompt)
        mcq_text = mcq_response.text.strip()

        # Clean markdown formatting
        if mcq_text.startswith("```json"):
            mcq_text = mcq_text[7:]
        if mcq_text.startswith("```"):
            mcq_text = mcq_text[3:]
        if mcq_text.endswith("```"):
            mcq_text = mcq_text[:-3]
        mcq_text = mcq_text.strip()

        # Try parsing JSON
        try:
            mcq_questions = json.loads(mcq_text)
        except json.JSONDecodeError:
            match = re.search(r"\[.*\]", mcq_text, re.DOTALL)
            if match:
                mcq_questions = json.loads(match.group())
            else:
                mcq_questions = [
                    {
                        "question": "Failed to generate questions. Please try again.",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "Option A",
                    }
                ]

        # ✅ Save image and summary in DB
        summary_entry = Summary(
            student_register_no="unknown",  # Or pass from frontend/form
            image_data=image_data,
            image_name=file.filename,
            description=summary,  # storing the generated summary
        )
        db.add(summary_entry)
        db.commit()
        db.refresh(summary_entry)

        return JSONResponse(
            {
                "message": "Image processed and stored successfully",
                "summary_id": summary_entry.id,
                "extracted_text": extracted_text,
                "summary": summary,
                "mcq_questions": mcq_questions,
            }
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

    finally:
        db.close()
